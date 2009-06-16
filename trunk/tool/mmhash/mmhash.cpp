#include <Python.h>
#include <stdint.h>
#include "MurmurHash2_64.cpp"
static PyObject * get_unsigned_hash(PyObject *self,PyObject *args) {
    char * guid;
    int len;
    if(!PyArg_ParseTuple(args,"s#",&guid,&len)) {
        return NULL;
    }
    uint32_t h =  MurmurHash2(guid,strlen(guid));
    /* return Py_BuildValue("l",h); */
    return PyLong_FromUnsignedLong(h);
}

static PyObject * get_hash(PyObject *self,PyObject *args) {
    char * guid;
    int len;
    if(!PyArg_ParseTuple(args,"s#",&guid,&len)) {
        return NULL;
    }
    int32_t h =  MurmurHash2(guid,strlen(guid));
    /* return Py_BuildValue("l",h); */
#if defined(__x86_64__) || defined(_M_X64)
    return PyInt_FromLong(h);
#else:
    return PyLong_FromLong(h);
#endif
}


static PyMethodDef methods[] = {
    {"get_hash",(PyCFunction)get_hash,METH_VARARGS,NULL},
    {"get_unsigned_hash",(PyCFunction)get_unsigned_hash,METH_VARARGS,NULL},
    {NULL,NULL,0,NULL}
};

PyMODINIT_FUNC initmmhash() {
    Py_InitModule3("mmhash", methods, "MurmurHash2 hash algorithm extension module.");
}
