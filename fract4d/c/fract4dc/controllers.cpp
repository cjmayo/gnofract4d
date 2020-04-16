
#include "controllers.h"

#include <dlfcn.h>
#include <cassert>
#include <pthread.h>

#include "pf.h"

#include "model/site.h"
#include "model/calcfunc.h"

#include "fract4dc/pysite.h"
#include "fract4dc/loaders.h"
#include "fract4dc/colormaps.h"
#include "fract4dc/images.h"

void fractal_controller::free_resources() {
    // free the point function and lib hanlder
    pf_handle->vtbl->kill(pf_handle);
    dlclose(lib_handle);
    // release python objects
    Py_XDECREF(py_cmap);
    Py_XDECREF(py_image);
    // release others
    delete [] c_pos_params;
    // release allocations
    if (site) {
        delete site;
    }
}

fractal_controller::~fractal_controller() {
    free_resources();
}

void fractal_controller::set_message_handler(PyObject *message_handler) {
    if (site) {
        delete site;
    }
    site = new PySite(message_handler);
}

void fractal_controller::set_fd(int fd) {
    if (site) {
        delete site;
    }
    site = new FDSite(fd);
}

void fractal_controller::start_calculating(PyObject *pyimage, PyObject *pycmap, PyObject *pyparams, calc_options coptions) {
    c_pos_params = new double[N_PARAMS];
    if (!parse_posparams(pyparams, c_pos_params))
    {
        PyErr_SetString(PyExc_ValueError, "bad arguments passed to controller.start_calculating");
        return;
    }
    c_options = coptions;

    Py_XDECREF(py_cmap);
    py_cmap = pycmap;
    cmap = colormaps::cmap_fromcapsule(py_cmap);
    Py_XINCREF(py_cmap);

    Py_XDECREF(py_image);
    py_image = pyimage;
    image = images::image_fromcapsule(py_image);
    Py_XINCREF(py_image);

    auto calc_fn = [](void *data) mutable -> void* {
        fractal_controller *fc = (fractal_controller *)data;
        calc(
            fc->c_pos_params,
            fc->c_options.eaa,
            fc->c_options.maxiter,
            fc->c_options.nThreads,
            fc->pf_handle,
            fc->cmap,
            fc->c_options.auto_deepen,
            fc->c_options.auto_tolerance,
            fc->c_options.tolerance,
            fc->c_options.yflip,
            fc->c_options.periodicity,
            fc->c_options.dirty,
            0,
            fc->c_options.render_type,
            fc->c_options.warp_param,
            fc->image,
            fc->site
        );
        return nullptr;
    };

    if (coptions.asynchronous) {
        site->interrupt();
        site->wait();
        site->start();
        pthread_t tid;
        pthread_create(&tid, nullptr, calc_fn, (void *)this);
        assert(tid != 0);
        site->set_tid(tid);
    } else {
        Py_BEGIN_ALLOW_THREADS
        calc_fn((void *)this);
        Py_END_ALLOW_THREADS
    }
}

void fractal_controller::stop_calculating() {
    if (site) {
        site->interrupt();
    }
}

namespace controllers
{
    bool create_controller(PyObject *self, PyObject *args, FractalController *fc)
    {
        char *library_file_path;
        PyObject *py_formula_params, *py_location_params;

        if (!PyArg_ParseTuple(args, "sOO",
                            &library_file_path,
                            &py_formula_params,
                            &py_location_params))
        {
            PyErr_SetString(PyExc_ValueError, "Wrong parameters");
            return false;
        }

        // parse formula and position params
        int f_params_len = 0;
        struct s_param *f_params = parse_params(py_formula_params, &f_params_len);
        if (!f_params)
        {
            PyErr_SetString(PyExc_ValueError, "bad formula params passed to create_controller");
            return false;
        }
        double pos_params[N_PARAMS];
        if (!parse_posparams(py_location_params, pos_params))
        {
            PyErr_SetString(PyExc_ValueError, "bad arguments passed to create_controller");
            return false;
        }

        // load dynamic library
        void *lib_handle = dlopen(library_file_path, RTLD_NOW);
        if (NULL == lib_handle)
        {
            PyErr_SetString(PyExc_ValueError, dlerror());
            return false;
        }

        // create the point function handler from dynamic library
        pf_obj *(*pfn)(void);
        pfn = (pf_obj * (*)(void)) dlsym(lib_handle, "pf_new");
        if (NULL == pfn)
        {
            PyErr_SetString(PyExc_ValueError, dlerror());
            dlclose(lib_handle);
            return false;
        }
        pf_obj *p = pfn();

        // initialize the point function with the params
        p->vtbl->init(p, pos_params, f_params, f_params_len);
        free(f_params);  // todo: find a better way than freeying the mallocated memory in the parse_params function

        // set the properties of fractal controller
        fc->pf_handle = p;
        fc->lib_handle = lib_handle;

        return true;
    }
} // namespace controllers