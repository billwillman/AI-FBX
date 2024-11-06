import math
import operator

import inspect
class ModuleExportControlMixin:
    # Used by various helper scripts.
    pass

class IgnoredMixin(ModuleExportControlMixin):
    # Used by various helper scripts.
    pass

class IncludeMixin(ModuleExportControlMixin):
    # Used by various helper scripts.
    pass

class IncludeInstanceMixin(ModuleExportControlMixin):
    # Used by various helper scripts.
    pass

class LockedLiteral:
    def _lock(self):
        super(LockedLiteral, self).__setattr__("_locked", True)

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False):
            raise AttributeError(
                f"Cannot change attribute of immutable "
                f"{type(self).__name__!r} object")
        super(LockedLiteral, self).__setattr__(name, value)

    def __delattr__(self, name):
        if getattr(self, "_locked", False):
            raise AttributeError(
                f"Cannot change attribute of immutable "
                f"{type(self).__name__!r} object")
        super(LockedLiteral, self).__delattr__(name)


__all__ = ["ABCException", "ABCMeta", "abstractmethod", "abstractproperty"]

class ABCException(Exception):
    pass

class abstractmethod(IncludeMixin):
    def __init__(self, func):
        if not callable(func):
            raise ABCException(f"Function is not callable: {func}")
        self.func = func
        self.args = self.getargs(func)

    def __eq__(self, other):
        if isinstance(other, abstractmethod):
            return self.args == other.args
        else:
            return self.args == self.getargs(other)

    def __get__(self, instance, owner=None):
        return self.func

    @staticmethod
    def getargs(func):
        signature = inspect.signature(func)
        return [(param.name, param.kind) for param in
                signature.parameters.values()]

class abstractproperty(abstractmethod):
    def __get__(self, instance, owner=None):
        if instance is None:
            return self.func
        return self.func(instance)

    def __set__(self, instance, value):
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, property):
            return self.func.__name__ == other.fget.__name__
        return False

class ABCMeta(type):
    _trigger = True

    def __init__(cls, name, bases, attrs, **kwds):
        super(ABCMeta, cls).__init__(name, bases, attrs, **kwds)

        for supercls in cls.__bases__:
            if supercls is object:
                continue
            methods = {attr: v for attr, v in supercls.__dict__.items()
                       if isinstance(v, abstractmethod)}

            for method in methods:
                if cls._trigger and method not in attrs:
                    raise ABCException("Method has not been defined: " +
                                       repr(methods[method].func))

                if cls._trigger and methods[method] != attrs[method]:
                    raise ABCException("Function signature is not the same: " +
                                       repr(methods[method].func) + " and " +
                                       repr(attrs[method]))


########################################################################################################################

def conv(num):
    """Convert float to string and removing decimal place as necessary."""
    if isinstance(num, float) and num.is_integer():
        return str(int(num))
    return str(num)

class Vector(LockedLiteral, metaclass=ABCMeta):
    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(conv, self))})"
    def __str__(self):
        return f"{self.__class__.__name__}({', '.join(map(conv, self))})"

    def __getitem__(self, i):
        return list(self)[i]

    @abstractmethod
    def __iter__(self):
        pass

    def __list__(self):
        return list(iter(self))

    def __hash__(self):
        return hash(list(self))

    @abstractmethod
    def __len__(self):
        pass

    def __bool__(self):
        return all(self)

    @abstractmethod
    def _o1(self, f):
        pass

    @abstractmethod
    def _o2(self, other, f):
        pass

    @abstractmethod
    def _o2r(self, other, f):
        pass

    def __add__(self, other):
        return self._o2(other, operator.add)
    def __radd__(self, other):
        return self._o2r(other, operator.add)

    def __sub__(self, other):
        return self._o2(other, operator.sub)
    def __rsub__(self, other):
        return self._o2r(other, operator.sub)

    def __mul__(self, other):
        return self._o2(other, operator.mul)
    def __rmul__(self, other):
        return self._o2r(other, operator.mul)

    def __div__(self, other):
        return self._o2(other, operator.div)
    def __rdiv__(self, other):
        return self._o2r(other, operator.div)

    def __floordiv__(self, other):
        return self._o2(other, operator.floordiv)
    def __rfloordiv__(self, other):
        return self._o2r(other, operator.floordiv)

    def __truediv__(self, other):
        return self._o2(other, operator.truediv)
    def __rtruediv__(self, other):
        return self._o2r(other, operator.truediv)

    def __mod__(self, other):
        return self._o2(other, operator.mod)
    def __rmod__(self, other):
        return self._o2r(other, operator.mod)

    def __lshift__(self, other):
        return self._o2(other, operator.lshift)
    def __rlshift__(self, other):
        return self._o2r(other, operator.lshift)

    def __rshift__(self, other):
        return self._o2(other, operator.rshift)
    def __rrshift__(self, other):
        return self._o2r(other, operator.rshift)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return all(self._o2(other, operator.eq))
    def __ne__(self, other):
        return any(self._o2(other, operator.ne))
    def __gt__(self, other):
        return all(self._o2(other, operator.gt))
    def __lt__(self, other):
        return all(self._o2(other, operator.lt))
    def __ge__(self, other):
        return all(self._o2(other, operator.ge))
    def __le__(self, other):
        return all(self._o2(other, operator.le))

    def __and__(self, other):
        return self._o2(other, operator.and_)
    def __rand__(self, other):
        return self._o2r(other, operator.and_)

    def __or__(self, other):
        return self._o2(other, operator.or_)
    def __ror__(self, other):
        return self._o2r(other, operator.or_)

    def __xor__(self, other):
        return self._o2(other, operator.xor)
    def __rxor__(self, other):
        return self._o2r(other, operator.xor)

    def __neg__(self):
        return self._o1(operator.neg)

    def __pos__(self):
        return self._o1(operator.pos)

    def __abs__(self):
        return self.length

    def abs(self):
        return self._o1(abs)

    def __round__(self, other=None):
        return self._o2(other, round)

    def __invert__(self):
        return self._o1(operator.invert)

    @abstractproperty
    def length(self):
        pass

    @property
    def intTuple(self):
        """Return the x, y and z values of this vector as ints"""
        return tuple(map(int, self))

    @abstractmethod
    def replace(self, num, value):
        pass

class Vector3(Vector):
    def __init__(self, xOrList=None, y=None, z=None):
        super(Vector3, self).__init__()
        if xOrList is not None:
            if y is None:
                if hasattr(xOrList, "x") and hasattr(xOrList, "y") and hasattr(xOrList, "z"):
                    l = [xOrList.x, xOrList.y, xOrList.z]
                else:
                    l = xOrList
            else:
                if z is None:
                    raise ValueError("Expected 3 arguments, got 2")
                l = [xOrList, y, z]
        else:
            l = [0, 0, 0]
        l = [x if isinstance(x, (int, float)) else float(x) for x in l]
        self.x, self.y, self.z = l
        self._lock()

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __len__(self):
        return 3

    def _o1(self, f):
        """Unary operator"""
        return Vector3(f(self.x), f(self.y), f(self.z))

    def _o2(self, other, f):
        """Any two-operator operation where the left operand is a Vector3"""
        if isinstance(other, Vector3):
            return Vector3(f(self.x, other.x), f(self.y, other.y), f(self.z, other.z))
        elif isinstance(other, list):
            return Vector3(f(self.x, other[0]), f(self.y, other[1]), f(self.z, other[2]))
        else:
            return Vector3(f(self.x, other), f(self.y, other), f(self.z, other))

    def _o2r(self, other, f):
        """Any two-operator operation where the right operand is a Vector3"""
        if isinstance(other, list):
            return Vector3(f(other[0], self.x), f(other[1], self.y), f(other[2], self.z))
        else:
            return Vector3(f(other, self.x), f(other, self.y), f(other, self.z))

    def replace(self, num, value):
        l = list(self)
        l[num] = value
        return Vector3(l)

    def copy(self):
        """
        Makes a copy of the Vector3

        Returns
        -------
        Vector3
            A shallow copy of the vector

        """
        return Vector3(self.x, self.y, self.z)

    def getLengthSqrd(self):
        """
        Gets the length of the vector squared. This
        is much faster than finding the length.

        Returns
        -------
        float
            The length of the vector squared

        """
        return self.x ** 2 + self.y ** 2 + self.z ** 2

    @property
    def length(self):
        """Gets the magnitude of the vector"""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self):
        """
        Get a normalized copy of the vector, or Vector3(0, 0, 0)
        if the length is 0.

        Returns
        -------
        Vector3
            A normalized vector

        """
        length = self.length
        if length != 0:
            return 1 / length * self
        return self.copy()

    def getDistance(self, other):
        """
        The distance between this vector and the other vector

        Returns
        -------
        float
            The distance

        """
        return math.sqrt((self.x - other[0]) ** 2 + (self.y - other[1]) ** 2 + (self.z - other[2]) ** 2)

    def getDistSqrd(self, other):
        """
        The distance between this vector and the other vector, squared.
        It is more efficient to call this than to call
        :meth:`Vector3.getDistance` and square it.

        Returns
        -------
        float
            The squared distance

        """
        return (self.x - other[0]) ** 2 + (self.y - other[1]) ** 2 + (self.z - other[2]) ** 2

    def clamp(self, min, max):
        """
        Returns a clamped vector between two other vectors,
        resulting in the vector being as close to the
        edge of a bounding box created as possible.

        Parameters
        ----------
        min : Vector3
            Min vector
        max : Vector3
            Max vector

        Returns
        -------
        Vector3
            A vector inside or on the surface of the
            bounding box specified by min and max.

        """
        x = self.x
        if self.x < min.x:
            x = min.x
        elif self.x > max.x:
            x = max.x

        y = self.y
        if self.y < min.y:
            y = min.y
        elif self.y > max.y:
            y = max.y

        z = self.z
        if self.z < min.z:
            z = min.z
        elif self.z > max.z:
            z = max.z

        ret = Vector3(x, y, z)
        return ret

    def dot(self, other):
        """
        Dot product of two vectors.

        Parameters
        ----------
        other : Vector3
            Other vector

        Returns
        -------
        float
            Dot product of the two vectors

        """
        return self.x * other[0] + self.y * other[1] + self.z * other[2]

    def cross(self, other):
        """
        Cross product of two vectors

        Parameters
        ----------
        other : Vector3
            Other vector

        Returns
        -------
        Vector3
            Cross product of the two vectors

        """
        if isinstance(other, Vector3):
            x = self.y * other.z - self.z * other.y
            y = self.z * other.x - self.x * other.z
            z = self.x * other.y - self.y * other.x
        else:
            x = self.y * other[2] - self.z * other[1]
            y = self.z * other[0] - self.x * other[2]
            z = self.x * other[1] - self.y * other[0]
        return Vector3(x, y, z)

    @staticmethod
    def min(a, b):
        return a._o2(b, min)

    @staticmethod
    def max(a, b):
        return a._o2(b, max)

    @staticmethod
    def zero():
        """A vector of zero length"""
        return Vector3(0, 0, 0)

    @staticmethod
    def one():
        """A vector of ones"""
        return Vector3(1, 1, 1)

    @staticmethod
    def forward():
        """Vector3 pointing in the positive z axis"""
        return Vector3(0, 0, 1)

    @staticmethod
    def back():
        """Vector3 pointing in the negative z axis"""
        return Vector3(0, 0, -1)

    @staticmethod
    def left():
        """Vector3 pointing in the negative x axis"""
        return Vector3(-1, 0, 0)

    @staticmethod
    def right():
        """Vector3 pointing in the postive x axis"""
        return Vector3(1, 0, 0)

    @staticmethod
    def up():
        """Vector3 pointing in the postive y axis"""
        return Vector3(0, 1, 0)

    @staticmethod
    def down():
        """Vector3 pointing in the negative y axis"""
        return Vector3(0, -1, 0)

########################################################################################################################


class FQuat(LockedLiteral):
    """
    Class to represent a unit quaternion, also known as a versor.

    Parameters
    ----------
    w : float
        Real value of Quaternion
    x : float
        x coordinate of Quaternion
    y : float
        y coordinate of Quaternion
    z : float
        z coordinate of Quaternion

    """
    def __init__(self, w, x, y, z):
        self.w = w
        self.x = x
        self.y = y
        self.z = z
        self._lock()

    def __repr__(self):
        return f"FQuat({', '.join(map(conv, self))})"
    def __str__(self):
        return f"FQuat({', '.join(map(conv, self))})"

    def __getitem__(self, i):
        if i == 0:
            return self.w
        elif i == 1:
            return self.x
        elif i == 2:
            return self.y
        elif i == 3:
            return self.z
        raise IndexError()

    def __iter__(self):
        yield self.w
        yield self.x
        yield self.y
        yield self.z

    def __list__(self):
        return [self.w, self.x, self.y, self.z]

    def __len__(self):
        return 4

    def __hash__(self):
        return hash((self.w, self.x, self.y, self.z))

    def __eq__(self, other):
        if hasattr(other, "__getitem__") and len(other) == 4:
            return self.w == other[0] and self.x == other[1] and self.y == other[2] and self.z == other[3]
        else:
            return False

    def __ne__(self, other):
        if hasattr(other, "__getitem__") and len(other) == 4:
            return self.w != other[0] or self.x != other[1] or self.y != other[2] or self.z != other[3]
        else:
            return True

    def __mul__(self, other):
        if isinstance(other, FQuat):
            w = self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z
            x = self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y
            y = self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x
            z = self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
            return FQuat(w, x, y, z)
        elif isinstance(other, (int, float)):
            angle, axis = self.angleAxisPair
            return FQuat.FromAxis((angle * other) % 360, axis)
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            angle, axis = self.angleAxisPair
            return FQuat.FromAxis((angle / other) % 360, axis)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, FQuat):
            diff = (self * other.conjugate).normalized()
            return QuaternionDiff(*diff)

    def absDiff(self, other):
        return abs(other - self)

    def copy(self):
        """
        Deep copy of the Quaternion.

        Returns
        -------
        Quaternion
            A deep copy

        """
        return FQuat(self.w, self.x, self.y, self.z)

    def normalized(self):
        """
        A normalized Quaternion, for rotations.
        If the length is 0, then the identity
        quaternion is returned.

        Returns
        -------
        Quaternion
            A unit quaternion
        """
        length = math.sqrt(self.w ** 2 + self.x ** 2 +
                            self.y ** 2 + self.z ** 2)
        if length:
            return FQuat(self.w / length, self.x / length, self.y / length, self.z / length)
        else:
            return FQuat.identity()

    @property
    def conjugate(self):
        """The conjugate of a unit quaternion"""
        return FQuat(self.w, -self.x, -self.y, -self.z)

    def RotateVector(self, vector):
        """Rotate a vector by the quaternion"""
        other = FQuat(0, *vector)
        return Vector3(self * other * self.conjugate)

    @staticmethod
    def FromAxis(angle, a):
        """
        Create a quaternion from an angle and an axis.

        Parameters
        ----------
        angle : float
            Angle to rotate
        a : Vector3
            Axis to rotate about

        """
        DEG_TO_RAD = math.pi/180.0
        axis = a.normalized()
        cos = math.cos(angle / 2.0 * DEG_TO_RAD)
        sin = math.sin(angle / 2.0 * DEG_TO_RAD)
        return FQuat(cos, axis.x * sin, axis.y * sin, axis.z * sin)

    @staticmethod
    def Between(v1, v2):
        a = FQuat.FromDir(v1).conjugate
        b = FQuat.FromDir(v2)
        return a * b

    @staticmethod
    def FromDir(v):
        RAD_TO_DEG = 180.0/math.pi
        a = FQuat.FromAxis(
            math.atan2(v.x, v.z) * RAD_TO_DEG,
            Vector3.up())
        b = FQuat.FromAxis(
            math.atan2(-v.y, math.sqrt(v.z ** 2 + v.x ** 2)) * RAD_TO_DEG,
            Vector3.right())
        return a * b

    @property
    def angleAxisPair(self):
        """
        Gets the angle and axis pair. Tuple of form (angle, axis).

        """
        RAD_TO_DEG = 180.0 / math.pi
        angle = 2 * math.acos(self.w) * RAD_TO_DEG
        if angle == 0:
            return (0, Vector3.up())
        return (angle, Vector3(self).normalized())

    @staticmethod
    def Euler(vector):
        """
        Create a quaternion using Euler rotations.

        Parameters
        ----------
        vector : Vector3
            Euler rotations

        Returns
        -------
        Quaternion
            Generated quaternion

        """
        a = FQuat.FromAxis(vector.x, Vector3.right())
        b = FQuat.FromAxis(vector.y, Vector3.up())
        c = FQuat.FromAxis(vector.z, Vector3.forward())
        return b * a * c ## YXZ

    @property
    def eulerAngles(self)->Vector3:
        """Gets the Euler angles of the quaternion"""
        s = self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2
        r23 = 2 * (self.w * self.x - self.y * self.z)
        if r23 > 0.999999 * s:
            x = math.pi / 2
            y = 2 * math.atan2(self.y, self.x)
            z = 0
        elif r23 < -0.999999 * s:
            x = -math.pi / 2
            y = -2 * math.atan2(self.y, self.x)
            z = 0
        else:
            x = math.asin(r23)
            r13 = 2 * (self.w * self.y + self.z * self.x) / s
            r33 = 1 - 2 * (self.x ** 2 + self.y ** 2) / s
            r21 = 2 * (self.w * self.z + self.x * self.y) / s
            r22 = 1 - 2 * (self.x ** 2 + self.z ** 2) / s
            y = math.atan2(r13, r33)
            z = math.atan2(r21, r22)

        euler = [x, y, z]
        RAD_TO_DEG = 180.0/math.pi
        for i in range(3):
            euler[i] = (euler[i] * RAD_TO_DEG + 180) % 360 - 180
        return Vector3(euler)

    @staticmethod
    def identity():
        """Identity quaternion representing no rotation"""
        return FQuat(1, 0, 0, 0)

class QuaternionDiff:
    def __init__(self, w, x, y, z):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def __abs__(self):
        DEG_TO_RAD = math.pi / 180.0
        return abs(2 * math.acos(self.w) * DEG_TO_RAD)