#include <Python.h>
#include <stdint.h>

#define FNV_32_PRIME 0x01000193
//-----------------------------------------------------------------------------
// MurmurHash2, by Austin Appleby

// Note - This code makes a few assumptions about how your machine behaves -

// 1. We can read a 4-byte value from any address without crashing
// 2. sizeof(int) == 4

// And it has a few limitations -

// 1. It will not work incrementally.
// 2. It will not produce the same results on little-endian and big-endian
//    machines.

unsigned int MurmurHash2 ( const void * key, int len)
{
    // 'm' and 'r' are mixing constants generated offline.
    // They're not really 'magic', they just happen to work well.

    const unsigned int m = 0x5bd1e995;
    const int r = 24;

    // Initialize the hash to a 'random' value

    unsigned int h = FNV_32_PRIME ^ len;

    // Mix 4 bytes at a time into the hash

    const unsigned char * data = (const unsigned char *)key;

    while(len >= 4)
    {
        unsigned int k = *(unsigned int *)data;

        k *= m; 
        k ^= k >> r; 
        k *= m; 
        
        h *= m; 
        h ^= k;

        data += 4;
        len -= 4;
    }
    
    // Handle the last few bytes of the input array

    switch(len)
    {
    case 3: h ^= data[2] << 16;
    case 2: h ^= data[1] << 8;
    case 1: h ^= data[0];
            h *= m;
    };

    // Do a few final mixes of the hash to ensure the last few
    // bytes are well-incorporated.

    h ^= h >> 13;
    h *= m;
    h ^= h >> 15;

    return h;
} 


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
    return PyInt_FromLong(h);
}


static PyMethodDef methods[] = {
    {"get_hash",(PyCFunction)get_hash,METH_VARARGS,NULL},
    {"get_unsigned_hash",(PyCFunction)get_unsigned_hash,METH_VARARGS,NULL},
    {NULL,NULL,0,NULL}
};

PyMODINIT_FUNC initmmhash() {
    Py_InitModule3("mmhash", methods, "MurmurHash2 hash algorithm extension module.");
}
