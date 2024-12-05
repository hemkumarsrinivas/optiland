import numpy as np
from optiland.geometries.base import BaseGeometry


class Plane(BaseGeometry):
    """An infinite plane geometry.

    Args:
        cs (CoordinateSystem): The coordinate system of the plane geometry.
    """

    def __init__(self, coordinate_system):
        super().__init__(coordinate_system)
        self.radius = np.inf
        self.is_symmetric = True

    def sag(self, x=0, y=0):
        """Calculate the surface sag of the plane geometry.

        Args:
            x (float or np.ndarray, optional): The x-coordinate of the point
                on the plane. Defaults to 0.
            y (float or np.ndarray, optional): The y-coordinate of the point
                on the plane. Defaults to 0.

        Returns:
            Union[float, np.ndarray]: The surface sag of the plane at the
                given point.
        """
        if isinstance(y, np.ndarray):
            return np.zeros_like(y)
        return 0

    def distance(self, rays):
        """Find the propagation distance to the plane geometry.

        Args:
            rays (RealRays): The rays used to calculate the distance.

        Returns:
            np.ndarray: The propagation distance to the plane geometry for
                each ray.
        """
        t = -rays.z / rays.N

        # if rays do not hit plane, set to NaN
        t[t < 0] = np.nan

        return t

    def surface_normal(self, rays):
        """Find the surface normal of the plane geometry at the given points.

        Args:
            rays (RealRays): The rays used to calculate the surface normal.

        Returns:
            Tuple[float, float, float]: The surface normal of the plane
                geometry at each point.
        """
        return 0, 0, 1

    def to_dict(self):
        """Convert the plane geometry to a dictionary.

        Returns:
            dict: The dictionary representation of the plane geometry.
        """
        geometry_dict = super().to_dict()
        geometry_dict.update({
            'radius': np.inf,
        })
        return geometry_dict

    @classmethod
    def from_dict(cls, data):
        """Create a plane geometry from a dictionary.

        Args:
            data (dict): The dictionary representation of the plane geometry.

        Returns:
            Plane: The plane geometry.
        """
        return cls(data['cs'])
