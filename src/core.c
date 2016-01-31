/** \file core.c
 *  \brief Integration layer between the C core and Python functions.

 <table>
 <tr><td>Project Name:                                   </td>
     <td><b>MakeHuman</b>                                </td></tr>
 <tr><td>Product Home Page:                              </td>
     <td>http://www.makehuman.org/                       </td></tr>
 <tr><td>SourceForge Home Page:                          </td>
     <td>http://sourceforge.net/projects/makehuman/      </td></tr>
 <tr><td>Authors:                                        </td>
     <td>Paolo Colombo, Simone Re, Hans-Peter Dusel</td></tr>
 <tr><td>Copyright(c):                                   </td>
     <td>MakeHuman Team 2001-2010                        </td></tr>
 <tr><td>Licensing:                                      </td>
     <td>GPL3 (see also
         http://makehuman.wiki.sourceforge.net/Licensing)</td></tr>
 <tr><td>Coding Standards:                               </td>
     <td>See http://makehuman.wiki.sourceforge.net/DG_Coding_Standards
                                                         </td></tr>
 </table>

 This module contains functions that pass events up from the SDL core to
 Python and functions that process calls from Python back to C.
 There are also a small number of utility functions for allocating memory for
 lists of Integers, Strings, Floats and Objects.

 */

#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif
#ifdef __APPLE__
#include <Python/structmember.h>
#else
#include <structmember.h>
#endif

#ifndef FLT_MAX
#include <float.h>
#endif

#include "core.h"
#include "SDL_thread.h"

// Object3D attributes directly accessed by Python
static PyMemberDef Object3D_members[] =
{
    {"x", T_FLOAT, offsetof(Object3D, x), 0, "X translation"},
    {"y", T_FLOAT, offsetof(Object3D, y), 0, "Y translation"},
    {"z", T_FLOAT, offsetof(Object3D, z), 0, "Z translation"},
    {"rx", T_FLOAT, offsetof(Object3D, rx), 0, "X rotation"},
    {"ry", T_FLOAT, offsetof(Object3D, ry), 0, "Y rotation"},
    {"rz", T_FLOAT, offsetof(Object3D, rz), 0, "Z rotation"},
    {"sx", T_FLOAT, offsetof(Object3D, sx), 0, "X scale"},
    {"sy", T_FLOAT, offsetof(Object3D, sy), 0, "Y scale"},
    {"sz", T_FLOAT, offsetof(Object3D, sz), 0, "Z scale"},
    {"shadeless", T_UINT, offsetof(Object3D, shadeless), 0, "Whether this object is affected by scene lights or not."},
    {"texture", T_UINT, offsetof(Object3D, texture), 0, "A texture id or 0 if this object doesn't have a texture."},
    {"shader", T_UINT, offsetof(Object3D, shader), 0, "A shader id or 0 if this object doesn't have a shader."},
    {"visibility", T_INT, offsetof(Object3D, isVisible), 0, "Whether this object is currently visible or not."},
    {"cameraMode", T_INT, offsetof(Object3D, inMovableCamera), 0, "Whether this object uses the Movable or Fixed camera mode."},
    {"pickable", T_INT, offsetof(Object3D, isPickable), 0, "Whether this object can be picked."},
    {"solid", T_INT, offsetof(Object3D, isSolid), 0, "Whether this object is solid or wireframe."},
    {NULL}  /* Sentinel */
};

// Object3D Methods
static PyMethodDef Object3D_methods[] =
{
    {
        "setVertCoord", (PyCFunction)Object3D_setVertCoo, METH_VARARGS,
        ""
    },
    {
        "setNormCoord", (PyCFunction)Object3D_setNormCoo, METH_VARARGS,
        ""
    },
    {
        "setUVCoord", (PyCFunction)Object3D_setUVCoo, METH_VARARGS,
        ""
    },
    {
        "setColorIDComponent", (PyCFunction)Object3D_setColorIDComponent, METH_VARARGS,
        ""
    },
    {
        "setColorComponent", (PyCFunction)Object3D_setColorComponent, METH_VARARGS,
        ""
    },
    {NULL}  /* Sentinel */
};

// Object3D attributes indirectly accessed by Python
static PyGetSetDef Object3D_getset[] =
{
    {"shaderParameters", (getter)Object3D_getShaderParameters, (setter)NULL, "The dictionary containing the shader parameters, read only.", NULL},
    {"translation", (getter)Object3D_getTranslation, (setter)Object3D_setTranslation, "The translation of the object as a 3 component vector.", NULL},
    {"rotation", (getter)Object3D_getRotation, (setter)Object3D_setRotation, "The rotation of the object as a 3 component vector.", NULL},
    {"scale", (getter)Object3D_getScale, (setter)Object3D_setScale, "The scale of the object as a 3 component vector.", NULL},
    {"transparentPrimitives", (getter)Object3D_getTransparentPrimitives, (setter)Object3D_setTransparentPrimitives, "How many of the primitives are transparent, transparent primitives are always at the end.", NULL},
    {"vertsPerPrimitive", (getter)Object3D_getVertsPerPrimitive, (setter)Object3D_setVertsPerPrimitive, "How many vertices each primitive has.", NULL},
	{"transform", (getter)Object3D_getTransform, (setter)NULL, "The transform of the object.", NULL},
    {NULL}
};

// Object3D type definition
PyTypeObject Object3DType =
{
    PyObject_HEAD_INIT(NULL)
    0,                                        // ob_size
    "mh.object3D",                            // tp_name
    sizeof(Object3D),                         // tp_basicsize
    0,                                        // tp_itemsize
    (destructor)Object3D_dealloc,             // tp_dealloc
    0,                                        // tp_print
    0,                                        // tp_getattr
    0,                                        // tp_setattr
    0,                                        // tp_compare
    0,                                        // tp_repr
    0,                                        // tp_as_number
    0,                                        // tp_as_sequence
    0,                                        // tp_as_mapping
    0,                                        // tp_hash
    0,                                        // tp_call
    0,                                        // tp_str
    0,                                        // tp_getattro
    0,                                        // tp_setattro
    0,                                        // tp_as_buffer
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, // tp_flags
    "Object3D object",                        // tp_doc
    0,		                                    // tp_traverse
    0,		                                    // tp_clear
    0,		                                    // tp_richcompare
    0,		                                    // tp_weaklistoffset
    0,		                                    // tp_iter
    0,		                                    // tp_iternext
    Object3D_methods,                         // tp_methods
    Object3D_members,                         // tp_members
    Object3D_getset,                          // tp_getset
    0,                                        // tp_base
    0,                                        // tp_dict
    0,                                        // tp_descr_get
    0,                                        // tp_descr_set
    0,                                        // tp_dictoffset
    (initproc)Object3D_init,                  // tp_init
    0,                                        // tp_alloc
    Object3D_new,                             // tp_new
};

/** \brief Registers the Object3D object in the Python environment.
 *  \param module The module to register the Object3D object in.
 *
 *  This function registers the Object3D object in the Python environment.
 */
void RegisterObject3D(PyObject *module)
{
    if (PyType_Ready(&Object3DType) < 0)
        return;

    Py_INCREF(&Object3DType);
    PyModule_AddObject(module, "Object3D", (PyObject*)&Object3DType);
}

/** \brief Takes care of the deallocation of the vertices, faces and text the Object3D object.
 *  \param self The Object3D object which is being deallocated.
 *
 *  This function takes care of the deallocation of the vertices, faces and text the Object3D object.
 */
void Object3D_dealloc(Object3D *self)
{
    // Free our data
    free(self->primitives);
    free(self->verts);
    free(self->norms);
    free(self->UVs);
    free(self->colors);
    free(self->colors2);

    // Free Python data
    self->ob_type->tp_free((PyObject*)self);
}

/** \brief Takes care of the initialization of the Object3D object members.
 *  \param self The Object3D object which is being initialized.
 *
 *  This function takes care of the initialization of the Object3D object members.
 */
PyObject *Object3D_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    // Alloc Python data
    Object3D *self = (Object3D*)type->tp_alloc(type, 0);

    // Init our data
    if (self)
    {
        self->shadeless = 0;
        self->texture = 0;
        self->shader = 0;
        self->vertsPerPrimitive = 4;
        self->shaderParameters = NULL;
        self->isVisible = 1;
        self->inMovableCamera = 1;
        self->isPickable = 1;
        self->isSolid = 1;

        self->x = 0.0;
        self->y = 0.0;
        self->z = 0.0;
        self->rx = 0.0;
        self->ry = 0.0;
        self->rz = 0.0;
        self->sx = 1.0;
        self->sy = 1.0;
        self->sz = 1.0;

        self->primitives = NULL;
        self->verts = NULL;
        self->norms = NULL;
        self->UVs = NULL;
        self->colors = NULL;
        self->colors2 = NULL;

        self->nPrimitives = 0;
        self->primitivesSize = 0;
        self->nTransparentPrimitives = 0;
        self->nVerts = 0;
        self->nNorms = 0;
        self->nColors = 0;
        self->nColors2 = 0;
    }

    return (PyObject*)self;
}

/** \brief The constructor of the Object3D object.
 *  \param self The Object3D object which is being constructed.
 *  \param args The arguments.
 *
 *  The constructor of the Object3D object. It allocates the vertex and face arrays.
 */
int Object3D_init(Object3D *self, PyObject *args, PyObject *kwds)
{
    int numVerts;
    PyObject *indexBuffer;

    if (!PyArg_ParseTuple(args, "iO", &numVerts, &indexBuffer) || !PyList_Check(indexBuffer))
        return -1;

    // Allocate arrays
    self->verts = makeFloatArray(numVerts * 3);
    self->norms = makeFloatArray(numVerts * 3);
    self->colors = makeUCharArray(numVerts * 3);
    self->colors2 = makeUCharArray(numVerts * 4);
    self->UVs = makeFloatArray(numVerts * 2);

    self->nVerts = numVerts;

    self->primitivesSize = (int)PyList_Size(indexBuffer);
    self->primitives = makeIntArray(self->primitivesSize);
    self->nNorms = numVerts * 3;
    self->nPrimitives = self->primitivesSize / self->vertsPerPrimitive;
    self->nColors = numVerts * 3;
    self->nColors2 = numVerts * 4;

    // Copy face indices
    {
        PyObject *iterator = PyObject_GetIter(indexBuffer);
        PyObject *item;
        int index = 0;

        for (item = PyIter_Next(iterator); item; item = PyIter_Next(iterator))
        {
            self->primitives[index++] = PyInt_AsLong(item);
            Py_DECREF(item);
        }

        Py_DECREF(iterator);
    }

    return 0;
}

/** \brief Sets a single coordinate value (x, y or z) for a vertex in G.world.
 *  \param objIndex an int containing the index of the 3D object that contains this vertex.
 *  \param vIdx an int indexing the vertex coordinate component to update.
 *  \param x a float specifying the X component of the value to be assigned to this vertex coordinate
 *           in the G.world array.
 *  \param y a float specifying the Y component of the value to be assigned to this vertex coordinate
 *           in the G.world array.
 *  \param z a float specifying the Z component of the value to be assigned to this vertex coordinate
 *           in the G.world array.
 *
 *  This function sets the value of a G.world coordinate component (x, y or z).
 *  This function is called indirectly by the setVertCoord Python wrapper.
 *  The Python wrapper specifies a list of the three coordinates, but this list is split up into 3
 *  separate calls to this function by the mh_setVertCoord function in main.c.
 */
PyObject *Object3D_setVertCoo(Object3D *self, PyObject *args)
{
    float x, y, z;
    int index;

    if (!PyArg_ParseTuple(args, "i(fff)", &index, &x, &y, &z))
        return NULL;

    if (index < 0 || index >= self->nVerts)
    {
        PyErr_Format(PyExc_IndexError, "index out of range, %i is not between 0 and %i", index, self->nVerts);
        return NULL;
    }

    self->verts[index * 3] = x;
    self->verts[index * 3 + 1] = y;
    self->verts[index * 3 + 2] = z;

    return Py_BuildValue("");
}

/** \brief Sets a single normal component value (x, y or z) for a vertex in G.world.
 *  \param objIndex an int containing the index of the 3D object that contains this vertex.
 *  \param nIdx an int indexing the vertex normal component to update.
 *  \param x a float specifying the X component of the value to be assigned to this normal
 *           in the G.world array.
 *  \param y a float specifying the Y component of the value to be assigned to this normal
 *           in the G.world array.
 *  \param z a float specifying the Z component of the value to be assigned to this normal
 *           in the G.world array.
 *
 *  This function sets the value of a G.world normal component (x, y or z).
 *  This function is called indirectly by the setNormCoord Python wrapper.
 *  The Python wrapper specifies a list of the three components, but this list is split up into 3
 *  separate calls to this function by the mh_setNormCoord function in main.c.
 */
PyObject *Object3D_setNormCoo(Object3D *self, PyObject *args)
{
    float x, y, z;
    int index;

    if (!PyArg_ParseTuple(args, "i(fff)", &index, &x, &y, &z))
        return NULL;

    if (index < 0 || index >= self->nVerts)
    {
        PyErr_Format(PyExc_IndexError, "index out of range, %i is not between 0 and %i", index, self->nVerts);
        return NULL;
    }

    self->norms[index * 3] = x;
    self->norms[index * 3 + 1] = y;
    self->norms[index * 3 + 2] = z;

    return Py_BuildValue("");
}

/** \brief Sets a single UV component value (U or V) for a vertex in G.world.
 *  \param objIndex an int containing the index of the 3D object that contains this vertex.
 *  \param nIdx an int indexing the vertex UV component to update.
 *  \param u a float specifying the value to be assigned to the U component of the UV mapping data
 *         associated with the specified vertex in the G.world array.
 *  \param v a float specifying the value to be assigned to the V component of the UV mapping data
 *         associated with the specified vertex in the G.world array.
 *
 *  This function sets the value of a G.world UV component (U or V).
 *  This function is called indirectly by the setUVCoord Python wrapper.
 *  The Python wrapper specifies a list of the two components, but this list is split up into 2
 *  separate calls to this function by the mh_setUVCoord function in main.c.
 */
PyObject *Object3D_setUVCoo(Object3D *self, PyObject *args)
{
    float u, v;
    int index;

    if (!PyArg_ParseTuple(args, "i(ff)", &index, &u, &v))
        return NULL;

    if (index < 0 || index >= self->nVerts)
    {
        PyErr_Format(PyExc_IndexError, "index out of range, %i is not between 0 and %i", index, self->nVerts);
        return NULL;
    }

    self->UVs[index * 2] = u;
    self->UVs[index * 2 + 1] = v;

    return Py_BuildValue("");
}

/** \brief Sets a single color component value (R, G or B) for a vertex in G.world.
 *  \param objIndex an int containing the index of the 3D object that contains this vertex.
 *  \param nIdx an int indexing the vertex color component to update.
 *  \param r an unsigned char (an integer value from 0-255) specifying the Red channel
 *         component to be assigned to this color component.
 *  \param g an unsigned char (an integer value from 0-255) specifying the Green channel
 *         component to be assigned to this color component.
 *  \param b an unsigned char (an integer value from 0-255) specifying the Blue channel
 *         component to be assigned to this color component.
 *
 *  This function sets the value of a G.world color component (R, G or B).
 *  This function is called by the mh_setColorCoord function in main.c which
 *  splits a list of the three color components into 3 separate calls to this function.
 *
 */
PyObject *Object3D_setColorIDComponent(Object3D *self, PyObject *args)
{
    unsigned char r, g, b;
    int index;

    if (!PyArg_ParseTuple(args, "i(BBB)", &index, &r, &g, &b))
        return NULL;

    if (index < 0 || index >= self->nVerts)
    {
        PyErr_Format(PyExc_IndexError, "index out of range, %i is not between 0 and %i", index, self->nVerts);
        return NULL;
    }

    self->colors[index * 3] = r;
    self->colors[index * 3 + 1] = g;
    self->colors[index * 3 + 2] = b;

    return Py_BuildValue("");
}

/** \brief Sets a single color component value (R, G, B or A) for a vertex in G.world.
 *  \param objIndex an int containing the index of the 3D object that contains this vertex.
 *  \param nIdx an int indexing the vertex color component to update.
 *  \param r an unsigned char (an integer value from 0-255) specifying the Red channel
 *         component to be assigned to this color component in the G.world array.
 *  \param g an unsigned char (an integer value from 0-255) specifying the Green channel
 *         component to be assigned to this color component in the G.world array.
 *  \param b an unsigned char (an integer value from 0-255) specifying the Blue channel
 *         component to be assigned to this color component in the G.world array.
 *  \param a an unsigned char (an integer value from 0-255) specifying the Alpha channel
 *         component to be assigned to this color component in the G.world array.
 *
 *  This function sets the value of a G.world color component (R, G, B or A).
 */
PyObject *Object3D_setColorComponent(Object3D *self, PyObject *args)
{
    unsigned char r, g, b, a;
    int index;

    if (!PyArg_ParseTuple(args, "i(BBBB)", &index, &r, &g, &b, &a))
        return NULL;

    if (index < 0 || index >= self->nVerts)
    {
        PyErr_Format(PyExc_IndexError, "index out of range, %i is not between 0 and %i", index, self->nVerts);
        return NULL;
    }

    self->colors2[index * 4] = r;
    self->colors2[index * 4 + 1] = g;
    self->colors2[index * 4 + 2] = b;
    self->colors2[index * 4 + 3] = a;

    return Py_BuildValue("");
}

/** \brief Gets the shader parameter dictionary for this Object3D object.
 *  \param self An 3D object.
 *
 *  This function gets  the shader parameter dictionary for this Object3D object.
 */
PyObject *Object3D_getShaderParameters(Object3D *self, void *closure)
{
    if (!self->shaderParameters)
        self->shaderParameters = PyDict_New();

    Py_INCREF(self->shaderParameters);
    return self->shaderParameters;
}

/** \brief Gets the translation for this Object3D object as a list.
 *  \param self The 3D object.
 *
 *  This function gets the translation for this Object3D object as a list.
 */
PyObject *Object3D_getTranslation(Object3D *self, void *closure)
{
    return Py_BuildValue("[f,f,f]", self->x, self->y, self->z);
}

/** \brief Sets the translation for this Object3D object as a list.
 *  \param self The 3D object.
 *  \param self The new translation as a python list.
 *
 *  This function sets the translation for this Object3D object as a list.
 */
int Object3D_setTranslation(Object3D *self, PyObject *value)
{
    if (!PySequence_Check(value))
        return -1;

    if (PySequence_Size(value) != 3)
    {
        PyErr_BadArgument();
        return -1;
    }

    self->x = (float)PyFloat_AsDouble(PySequence_GetItem(value, 0));
    self->y = (float)PyFloat_AsDouble(PySequence_GetItem(value, 1));
    self->z = (float)PyFloat_AsDouble(PySequence_GetItem(value, 2));

    return 0;
}

/** \brief Gets the rotation for this Object3D object as a list.
 *  \param self The 3D object.
 *
 *  This function gets the rotation for this Object3D object as a list.
 */
PyObject *Object3D_getRotation(Object3D *self, void *closure)
{
    return Py_BuildValue("[f,f,f]", self->rx, self->ry, self->rz);
}

/** \brief Sets the rotation for this Object3D object as a list.
 *  \param self The 3D object.
 *  \param self The new rotation as a python list.
 *
 *  This function sets the rotation for this Object3D object as a list.
 */
int Object3D_setRotation(Object3D *self, PyObject *value)
{
    if (!PySequence_Check(value))
        return -1;

    if (PySequence_Size(value) != 3)
    {
        PyErr_BadArgument();
        return -1;
    }

    self->rx = (float)PyFloat_AsDouble(PySequence_GetItem(value, 0));
    self->ry = (float)PyFloat_AsDouble(PySequence_GetItem(value, 1));
    self->rz = (float)PyFloat_AsDouble(PySequence_GetItem(value, 2));

    return 0;
}

/** \brief Gets the scale for this Object3D object as a list.
 *  \param self The 3D object.
 *
 *  This function gets the scale for this Object3D object as a list.
 */
PyObject *Object3D_getScale(Object3D *self, void *closure)
{
    return Py_BuildValue("[f,f,f]", self->sx, self->sy, self->sz);
}

/** \brief Sets the scale for this Object3D object as a list.
 *  \param self The 3D object.
 *  \param self The new scale as a python list.
 *
 *  This function sets the scale for this Object3D object as a list.
 */
int Object3D_setScale(Object3D *self, PyObject *value)
{
    if (!PySequence_Check(value))
        return -1;

    if (PySequence_Size(value) != 3)
    {
        PyErr_BadArgument();
        return -1;
    }

    self->sx = (float)PyFloat_AsDouble(PySequence_GetItem(value, 0));
    self->sy = (float)PyFloat_AsDouble(PySequence_GetItem(value, 1));
    self->sz = (float)PyFloat_AsDouble(PySequence_GetItem(value, 2));

    return 0;
}

PyObject * Object3D_getTransparentPrimitives( Object3D *self, void *closure)
{
    return Py_BuildValue("i", self->nTransparentPrimitives);
}

int Object3D_setTransparentPrimitives( Object3D *self, PyObject *value)
{
    int transparentPrimitives = PyInt_AsLong(value);

    if (transparentPrimitives < 0)
    {
        PyErr_Format(PyExc_RuntimeError, "Trying to set transparentQuads to %i", transparentPrimitives);
        return -1;
    }

    if (transparentPrimitives > self->nPrimitives)
    {
        PyErr_Format(PyExc_RuntimeError, "Trying to set transparentQuads to %i while there are only %i quads", transparentPrimitives, self->nPrimitives);
        return -1;
    }

    self->nTransparentPrimitives = transparentPrimitives;

    return 0;
}

PyObject * Object3D_getVertsPerPrimitive( Object3D *self, void *closure)
{
    return Py_BuildValue("i", self->vertsPerPrimitive);
}

int Object3D_setVertsPerPrimitive( Object3D *self, PyObject *value)
{
    int vertsPerPrimitive = PyInt_AsLong(value);

    if (vertsPerPrimitive < 1 || vertsPerPrimitive > 4)
    {
        PyErr_Format(PyExc_RuntimeError, "Trying to set vertsPerPrimitive to %i while only values between 1 and 4 inclusive are allowed", vertsPerPrimitive);
        return -1;
    }

    self->vertsPerPrimitive = vertsPerPrimitive;
    self->nPrimitives = self->primitivesSize / self->vertsPerPrimitive;

    return 0;
}

static int distanceSort(const void *a, const void *b)
{
    float d1 = ((SortStruct*)a)->distance;
    float d2 = ((SortStruct*)b)->distance;

    if (d1 < d2)
        return 1;
    else if (d1 > d2)
        return -1;
    else
        return 0;
}

void Object3D_sortFaces(Object3D *self)
{
    Camera *camera = (Camera*)PyList_GET_ITEM(G.cameras, 0);

    float cx = camera->eyeX, cy = camera->eyeY, cz = camera->eyeZ;
    float tx, ty, tz;
    float alpha, s, c;
    float x, y, z;
    int *indices = self->primitives + self->nPrimitives - self->nTransparentPrimitives;
    float *verts;
    int i;
    int n;
    float distance, d;

    // Rotate camera position according to object position
    // This is less costly that transforming all points
    cx -= self->x;
    cy -= self->y;
    cz -= self->z;

    // Rotate X
    alpha = (float)(-self->rx * 3.141592653589793238462643 / 180.0);
    c = cosf(alpha);
    s = sinf(alpha);
    tx = cx;
    ty = cy*c - cz*s;
    tz = cy*s + cz*c;

    // Rotate Y
    alpha = (float)(-self->ry * 3.141592653589793238462643 / 180.0);
    c = cosf(alpha);
    s = sinf(alpha);
    cx = tz*s + tx*c;
    cy = ty;
    cz = tz*c - tx*s;

    // Rotate Z
    alpha = (float)(-self->rz * 3.141592653589793238462643 / 180.0);
    c = cosf(alpha);
    s = sinf(alpha);
    tx = cx*c - cy*s;
    ty = cx*s + cy*c;
    tz = cz;

    cx = tx + self->x;
    cy = ty + self->y;
    cz = tz + self->z;

    // Resize sorting data if needed
    if (G.nSortData < self->nTransparentPrimitives)
    {
        G.nSortData = self->nTransparentPrimitives;
        G.sortData = realloc(G.sortData, G.nSortData * sizeof(SortStruct));
    }

    // Prepare sorting data
    for (i = 0; i < self->nTransparentPrimitives; i++)
    {
#if 0
        // Calculate center
        x = y = z = 0.0;

        for (n = 0; n < 4; n++)
        {
            G.sortData[i].indices[n] = *quads;
            verts = &self->verts[*quads * 3];
            x += *verts++;
            y += *verts++;
            z += *verts++;
            quads++;
        }

        x /= 4.0;
        y /= 4.0;
        z /= 4.0;

        // Calculate distance from center
        x -= cx;
        y -= cy;
        z -= cz;

        distance = =x*x+y*y+z*z;
#else
        // Calculate distance of closest vertex
        distance = FLT_MAX;

        for (n = 0; n < 4; n++)
        {
            G.sortData[i].indices[n] = *indices;
            verts = &self->verts[*indices * 3];
            x = *verts++ - cx;
            y = *verts++ - cy;
            z = *verts++ - cz;
            indices++;

            d = x*x+y*y+z*z;

            if (d < distance)
                distance = d;
        }
#endif

        G.sortData[i].distance = distance;
    }

    // Sort
    qsort(G.sortData, self->nTransparentPrimitives, sizeof(SortStruct), distanceSort);

    // Copy to buffer
    indices = self->primitives + self->nPrimitives - self->nTransparentPrimitives;
    for (i = 0; i < self->nTransparentPrimitives; i++)
    {
        for (n = 0; n < 4; n++)
        {
            *indices++ = G.sortData[i].indices[n];
        }
    }
}

/** \brief Invokes the Python mouseButtonDown function.
 *  \param b an int indicating which button this event relates to.
 *  \param x an int specifying the horizontal mouse pointer position in the GUI window (in pixels).
 *  \param y an int specifying the vertical mouse pointer position in the GUI window (in pixels).
 *
 *  This function invokes the Python mouseButtonDown function when the SDL
 *  module detects a mouse button down event.
 */
void callMouseButtonDown(int b, int x, int y)
{
    if (G.mouseDownCallback && !PyObject_CallFunction(G.mouseDownCallback, "iii", b, x, y))
        PyErr_Print();
}

/** \brief Invokes the Python mouseButtonUp function.
 *  \param b an int indicating which button this event relates to.
 *  \param x an int specifying the horizontal mouse pointer position in the GUI window (in pixels).
 *  \param y an int specifying the vertical mouse pointer position in the GUI window (in pixels).
 *
 *  This function invokes the Python mouseButtonUp function when the SDL
 *  module detects a mouse button up event.
 */
void callMouseButtonUp(int b, int x, int y)
{
    if (G.mouseUpCallback && !PyObject_CallFunction(G.mouseUpCallback, "iii", b, x, y))
        PyErr_Print();
}

/** \brief Invokes the Python mouseMotion function.
 *  \param s an int indicating the mouse.motion.state of the event (1=Mouse moved, 0=Mouse click)..
 *  \param x an int specifying the horizontal mouse pointer position in the GUI window (in pixels).
 *  \param y an int specifying the vertical mouse pointer position in the GUI window (in pixels).
 *  \param xrel an int specifying the difference between the previously recorded horizontal mouse
 *         pointer position in the GUI window and the current position (in pixels).
 *  \param yrel an int specifying the difference between the previously recorded vertical mouse
 *         pointer position in the GUI window and the current position (in pixels).
 *
 *  This function invokes the Python mouseMotion function when the SDL
 *  module detects movement of the mouse.
 */
void callMouseMotion(int s, int x, int y, int xrel, int yrel)
{
    if (G.mouseMovedCallback && !PyObject_CallFunction(G.mouseMovedCallback, "iiiii", s, x, y, xrel, yrel))
        PyErr_Print();
}

/** \brief Invokes the Python keyDown function.
 *  \param key an int containing the key code of the key pressed.
 *  \param character an unsigned short character containing the Unicode character corresponding to the key pressed.
 *
 *  This function invokes the Python keyDown function when the SDL
 *  module detects a standard keyboard event, ie. when a standard character key is pressed.
 */
void callKeyDown(int key, unsigned short character, int modifiers)
{
    if (G.keyDownCallback &&
#ifdef __WIN32__
            !PyObject_CallFunction(G.keyDownCallback, "iu#i", key, &character, 1, modifiers))
#else
            !PyObject_CallFunction(G.keyDownCallback, "ici", key, key, modifiers))
#endif
        PyErr_Print();
}

void callKeyUp(int key, unsigned short character, int modifiers)
{
    if (G.keyUpCallback &&
#ifdef __WIN32__
            !PyObject_CallFunction(G.keyUpCallback, "iu#i", key, &character, 1, modifiers))
#else
            !PyObject_CallFunction(G.keyUpCallback, "ici", key, key, modifiers))
#endif
        PyErr_Print();
}

void callResize(int w, int h, int fullscreen)
{
    if (G.resizeCallback && !PyObject_CallFunction(G.resizeCallback, "iii", w, h, fullscreen))
        PyErr_Print();
}

void callQuit()
{
  if (G.quitCallback && !PyObject_CallFunction(G.quitCallback, ""))
    PyErr_Print();
}

void setClearColor(float r, float g, float b, float a)
{
    G.clearColor[0] = r;
    G.clearColor[1] = g;
    G.clearColor[2] = b;
    G.clearColor[3] = a;
}

/** \brief Creates an array of n floats and returns a pointer to that array.
 *  \param n an int indicating the number of floats to add into the array.
 *
 *  This function creates an array of n floats each containing a value of 1.0 and returns a pointer to that array.
 */
float *makeFloatArray(int n)
{
    float *iptr;
    int i;
    iptr = (float *)malloc(n * sizeof(float));
    assert(iptr);
    if (NULL != iptr)
    {
        for (i = 0; i < n; i++)
        {
            iptr[i] = 1.0;
        }
    }
    else
    {
        printf ("Out of memory!\n");
    }
    return iptr;
}

/** \brief Creates an array of n characters and returns a pointer to that array.
 *  \param n an int indicating the number of characters to add into the array.
 *
 *  This function creates an array of n characters set to high values and returns a pointer to that array.
 */
unsigned char *makeUCharArray(int n)
{
    unsigned char *iptr;
    int i;
    iptr = (unsigned char *)malloc(n * sizeof(unsigned char));
    assert(iptr);
    if (NULL != iptr)
    {
        for (i = 0; i < n; i++)
        {
            iptr[i] = 255;
        }
    }
    else
    {
        printf ("Out of memory!\n");
        assert(0);
    }
    return iptr;
}

/** \brief Creates an array of n integers and returns a pointer to that array.
 *  \param n an int indicating the number of integers to add into the array.
 *
 *  This function creates an array of n integers set to '-1' and returns a pointer to that array.
 */
int *makeIntArray(int n)
{
    int *iptr;
    int i;
    iptr = (int *)malloc(n * sizeof(int));
    assert(iptr);
    if (NULL != iptr)
    {
        for (i = 0; i < n; i++)
        {
            iptr[i] = -1;
        }
    }
    else
    {
        printf ("Out of memory!\n");
    }
    return iptr;
}
