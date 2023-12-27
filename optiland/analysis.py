from copy import deepcopy
import numpy as np
import matplotlib.pyplot as plt


class SpotDiagram:
    # TODO: analysis fails when a single wavelength passed in a list

    def __init__(self, optic, fields='all', wavelengths='all', num_rings=6,
                 distribution='hexapolar'):
        self.optic = optic
        self.fields = fields
        self.wavelengths = wavelengths
        if self.fields == 'all':
            self.fields = self.optic.fields.get_field_coords()

        if self.wavelengths == 'all':
            self.wavelengths = self.optic.wavelengths.get_wavelengths()

        self.data = self._generate_data(self.fields, self.wavelengths,
                                        num_rings, distribution)

    def view(self, figsize=(12, 4)):

        N = self.optic.fields.num_fields
        num_rows = (N + 2) // 3

        fig, axs = plt.subplots(num_rows, 3,
                                figsize=(figsize[0], num_rows*figsize[1]),
                                sharex=True, sharey=True)
        axs = axs.flatten()

        # subtract centroid and find limits
        data = self._center_spots(deepcopy(self.data))
        geometric_size = self.geometric_spot_radius()
        axis_lim = np.max(geometric_size)

        # plot wavelengths for each field
        for k, field_data in enumerate(data):
            self._plot_field(axs[k], field_data, self.fields[k],
                             axis_lim, self.wavelengths)

        # remove empty axes
        for k in range(N, num_rows * 3):
            fig.delaxes(axs[k])

        plt.legend(bbox_to_anchor=(1.05, 0.5), loc='center left')

        plt.tight_layout()
        plt.show()

    def centroid(self):
        norm_index = self.optic.wavelengths.primary_index
        centroid = []
        for field_data in self.data:
            centroid_x = np.mean(field_data[norm_index][0])
            centroid_y = np.mean(field_data[norm_index][1])
            centroid.append((centroid_x, centroid_y))
        return centroid

    def geometric_spot_radius(self):
        data = self._center_spots(deepcopy(self.data))
        geometric_size = []
        for field_data in data:
            geometric_size_field = []
            for wave_data in field_data:
                r = np.sqrt(wave_data[0]**2 + wave_data[1]**2)
                geometric_size_field.append(np.max(r))
            geometric_size.append(geometric_size_field)
        return geometric_size

    def rms_spot_radius(self):
        data = self._center_spots(deepcopy(self.data))
        rms = []
        for field_data in data:
            rms_field = []
            for wave_data in field_data:
                r2 = wave_data[0]**2 + wave_data[1]**2
                rms_field.append(np.sqrt(np.mean(r2)))
            rms.append(rms_field)
        return rms

    def _center_spots(self, data):
        centroids = self.centroid()
        data = deepcopy(self.data)
        for i, field_data in enumerate(data):
            for wave_data in field_data:
                wave_data[0] -= centroids[i][0]
                wave_data[1] -= centroids[i][1]
        return data

    def _generate_data(self, fields, wavelengths, num_rays=100,
                       distribution='hexapolar'):
        data = []
        for field in fields:
            field_data = []
            for wavelength in wavelengths:
                field_data.append(self._generate_field_data(field,
                                                            wavelength,
                                                            num_rays,
                                                            distribution))
            data.append(field_data)
        return data

    def _generate_field_data(self, field, wavelength, num_rays=100,
                             distribution='hexapolar'):
        self.optic.trace(*field, wavelength, num_rays, distribution)
        x = self.optic.surface_group.x[-1, :]
        y = self.optic.surface_group.y[-1, :]
        return [x, y]

    def _plot_field(self, ax, field_data, field, axis_lim,
                    wavelengths, buffer=1.05):
        markers = ['o', 's', '^']
        for k, points in enumerate(field_data):
            ax.scatter(*points, s=10, label=f'{wavelengths[k]:.4f} µm',
                       marker=markers[k % 3], alpha=0.7)
            ax.axis('square')
            ax.set_xlabel('X (µm)')
            ax.set_ylabel('Y (µm)')
            ax.set_xlim((-axis_lim*buffer, axis_lim*buffer))
            ax.set_ylim((-axis_lim*buffer, axis_lim*buffer))
        ax.set_title(f'Hx: {field[0]:.3f}, Hy: {field[1]:.3f}')


class EncircledEnergy(SpotDiagram):

    def __init__(self, optic, fields='all', wavelength='primary',
                 num_rays=100_000, distribution='random', num_points=256):
        self.num_points = num_points
        if wavelength == 'primary':
            wavelength = optic.primary_wavelength

        super().__init__(optic, fields, [wavelength], num_rays, distribution)

        # self.ee, self.radius = 0

    def view(self, figsize=(7, 4.5)):
        fig, ax = plt.subplots(figsize=figsize)

        data = self._center_spots(deepcopy(self.data))
        geometric_size = self.geometric_spot_radius()
        axis_lim = np.max(geometric_size)
        for k, field_data in enumerate(data):
            self._plot_field(ax, field_data, self.fields[k],
                             axis_lim, self.num_points)

        ax.legend(bbox_to_anchor=(1.05, 0.5), loc='center left')
        ax.set_xlabel('Radius (mm)')
        ax.set_ylabel('Encircled Energy (-)')
        ax.set_title(f'Wavelength: {self.wavelengths[0]:.4f} µm')
        ax.set_xlim((0, None))
        ax.set_ylim((0, None))
        fig.tight_layout()
        plt.show()

    def centroid(self):
        centroid = []
        for field_data in self.data:
            centroid_x = np.mean(field_data[0][0])
            centroid_y = np.mean(field_data[0][1])
            centroid.append((centroid_x, centroid_y))
        return centroid

    def _encircled_energy(self, radii, energy, radius_max):
        return np.nansum(energy[radii <= radius_max])

    def _plot_field(self, ax, field_data, field, axis_lim,
                    num_points, buffer=1.2):
        r_max = axis_lim * buffer
        r_step = np.linspace(0, r_max, num_points)
        for points in field_data:
            x, y, energy = points
            radii = np.sqrt(x**2 + y**2)
            def vectorized_ee(r): return np.nansum(energy[radii <= r])
            ee = np.vectorize(vectorized_ee)(r_step)
            ax.plot(r_step, ee,
                    label=f'Hx: {field[0]:.3f}, Hy: {field[1]:.3f}')

    def _generate_encircled_energy_data(self, field_data, axis_lim,
                                        num_points, buffer=1.2):
        # TODO - complete
        r_max = axis_lim * buffer
        r_step = np.linspace(0, r_max, num_points)
        ee = []
        for points in field_data:
            x, y, energy = points
            radii = np.sqrt(x**2 + y**2)
            def vectorized_ee(r): return np.nansum(energy[radii <= r])
            ee.append(np.vectorize(vectorized_ee)(r_step))
        return r_step, ee

    def _generate_field_data(self, field, wavelength, num_rays=100,
                             distribution='hexapolar'):
        self.optic.trace(*field, wavelength, num_rays, distribution)
        x = self.optic.surface_group.x[-1, :]
        y = self.optic.surface_group.y[-1, :]
        energy = self.optic.surface_group.energy[-1, :]
        return [x, y, energy]


class RayFan:

    def __init__(self, optic, fields='all', wavelengths='all', num_points=256):
        self.optic = optic
        self.fields = fields
        self.wavelengths = wavelengths
        if num_points % 2 == 1:
            num_points += 1  # force to be odd so a point lies at P=0
        self.num_points = num_points

        if self.fields == 'all':
            self.fields = self.optic.fields.get_field_coords()

        if self.wavelengths == 'all':
            self.wavelengths = self.optic.wavelengths.get_wavelengths()

        self.data = self._generate_data()

    def view(self):
        _, axs = plt.subplots(nrows=len(self.fields), ncols=2,
                              figsize=(10, 10), sharex=True, sharey=True)

        Px = self.data['Px']
        Py = self.data['Py']

        for k, field in enumerate(self.fields):
            for wavelength in self.wavelengths:
                ex = self.data[f'{field}'][f'{wavelength}']['x']
                ey = self.data[f'{field}'][f'{wavelength}']['y']

                axs[k, 0].plot(Py, ey, zorder=3, label=f'{wavelength:.4f} µm')
                axs[k, 0].grid()
                axs[k, 0].axhline(y=0, lw=1, color='gray')
                axs[k, 0].axvline(x=0, lw=1, color='gray')
                axs[k, 0].set_xlabel('$P_y$')
                axs[k, 0].set_ylabel('$\\epsilon_y$ (mm)')
                axs[k, 0].set_xlim((-1, 1))
                axs[k, 0].set_title(f'Hx: {field[0]:.3f}, Hy: {field[1]:.3f}')

                axs[k, 1].plot(Px, ex, zorder=3, label=f'{wavelength:.4f} µm')
                axs[k, 1].grid()
                axs[k, 1].axhline(y=0, lw=1, color='gray')
                axs[k, 1].axvline(x=0, lw=1, color='gray')
                axs[k, 1].set_xlabel('$P_x$')
                axs[k, 1].set_ylabel('$\\epsilon_x$ (mm)')
                axs[k, 0].set_xlim((-1, 1))
                axs[k, 1].set_title(f'Hx: {field[0]:.3f}, Hy: {field[1]:.3f}')

        plt.legend(loc='upper center', bbox_to_anchor=(-0.1, -0.2), ncol=3)
        plt.subplots_adjust(top=1)
        plt.show()

    def _generate_data(self):
        data = {}
        data['Px'] = np.linspace(-1, 1, self.num_points)
        data['Py'] = np.linspace(-1, 1, self.num_points)
        for field in self.fields:
            Hx = field[0]
            Hy = field[1]

            data[f'{field}'] = {}
            for wavelength in self.wavelengths:
                data[f'{field}'][f'{wavelength}'] = {}

                self.optic.trace(Hx=Hx, Hy=Hy,
                                 wavelength=wavelength,
                                 num_rays=self.num_points,
                                 distribution='line_x')
                data[f'{field}'][f'{wavelength}']['x'] = \
                    self.optic.surface_group.x[-1, :]

                self.optic.trace(Hx=Hx, Hy=Hy,
                                 wavelength=wavelength,
                                 num_rays=self.num_points,
                                 distribution='line_y')
                data[f'{field}'][f'{wavelength}']['y'] = \
                    self.optic.surface_group.y[-1, :]

        # remove distortion
        wave_ref = self.optic.primary_wavelength
        for field in self.fields:
            x_offset = data[f'{field}'][f'{wave_ref}']['x'][self.num_points//2]
            y_offset = data[f'{field}'][f'{wave_ref}']['y'][self.num_points//2]
            for wavelength in self.wavelengths:
                data[f'{field}'][f'{wavelength}']['x'] -= x_offset
                data[f'{field}'][f'{wavelength}']['y'] -= y_offset

        return data


class YYbar:

    def __init__(self, optic, wavelength='primary'):
        self.optic = optic
        if wavelength == 'primary':
            wavelength = optic.primary_wavelength
        self.wavelength = wavelength

    def view(self, figsize=(7, 5.5)):
        _, ax = plt.subplots(figsize=figsize)

        ya, _ = self.optic.paraxial.marginal_ray()
        yb, _ = self.optic.paraxial.chief_ray()

        ya = ya.flatten()
        yb = yb.flatten()

        for k in range(2, len(ya)):
            label = ''
            if k == 2:
                label = 'Surface 1'
            elif k == len(ya)-1:
                label = 'Image'
            ax.plot([yb[k-1], yb[k]], [ya[k-1], ya[k]], label=label)

        ax.axhline(y=0, linewidth=0.5, color='k')
        ax.axvline(x=0, linewidth=0.5, color='k')
        ax.set_xlabel('Chief Ray Height (mm)')
        ax.set_ylabel('Marginal Ray Height (mm)')
        ax.legend()
        plt.show()


class Distortion:

    def __init__(self, optic, wavelengths='all', num_points=128,
                 distortion_type='f-tan'):
        self.optic = optic
        if wavelengths == 'all':
            wavelengths = self.optic.wavelengths.get_wavelengths()
        self.wavelengths = wavelengths
        self.num_points = num_points
        self.distortion_type = distortion_type
        self.data = self._generate_data()

    def view(self, figsize=(7, 5.5)):
        _, ax = plt.subplots(figsize=figsize)
        ax.axvline(x=0, color='k', linewidth=1, linestyle='--')

        field = np.linspace(1e-10, self.optic.fields.max_field,
                            self.num_points)
        for k, wavelength in enumerate(self.wavelengths):
            ax.plot(self.data[k], field, label=f'{wavelength:.4f} µm')
            ax.set_xlabel('Distortion (%)')
            ax.set_ylabel('Field')

        current_xlim = plt.xlim()
        plt.xlim([-max(np.abs(current_xlim)), max(np.abs(current_xlim))])
        plt.ylim([0, None])
        plt.legend(bbox_to_anchor=(1.05, 0.5), loc='center left')
        plt.show()

    def _generate_data(self):
        Hx = np.zeros(self.num_points)
        Hy = np.linspace(1e-10, 1, self.num_points)

        data = []
        for wavelength in self.wavelengths:
            self.optic.trace_generic(Hx=Hx, Hy=Hy, Px=0, Py=0,
                                     wavelength=wavelength)
            yr = self.optic.surface_group.y[-1, :]

            const = yr[0] / (np.tan(1e-10 *
                                    np.radians(self.optic.fields.max_field)))

            if self.distortion_type == 'f-tan':
                yp = const * np.tan(Hy *
                                    np.radians(self.optic.fields.max_field))
            elif self.distortion_type == 'f-theta':
                yp = const * np.tan(Hy *
                                    np.radians(self.optic.fields.max_field))
            else:
                raise ValueError('''Distortion type must be "f-tan" or
                                 "f-theta"''')

            data.append(100 * (yr - yp) / yp)

        return data


class GridDistortion:

    def __init__(self, optic, wavelength='primary', num_points=10,
                 distortion_type='f-tan'):
        self.optic = optic
        if wavelength == 'primary':
            wavelength = optic.primary_wavelength
        self.wavelength = wavelength
        self.num_points = num_points
        self.distortion_type = distortion_type
        self.data = self._generate_data()

    def view(self, figsize=(7, 5.5)):
        fig, ax = plt.subplots(figsize=figsize)

        ax.plot(self.data['xp'], self.data['yp'], 'C1', linewidth=1)
        ax.plot(self.data['xp'].T, self.data['yp'].T, 'C1', linewidth=1)

        ax.plot(self.data['xr'], self.data['yr'], 'C0P')
        ax.plot(self.data['xr'].T, self.data['yr'].T, 'C0P')

        ax.set_xlabel('Image X (mm)')
        ax.set_ylabel('Image Y (mm)')
        ax.set_aspect('equal', adjustable='box')

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        max_distortion = self.data['max_distortion']
        ax.set_title(f'Max Distortion: {max_distortion:.2f}%')
        fig.tight_layout()
        plt.show()

    def _generate_data(self):
        # trace single reference ray
        self.optic.trace_generic(Hx=0, Hy=1e-10, Px=0, Py=0,
                                 wavelength=self.wavelength)

        const = (self.optic.surface_group.y[-1, 0] /
                 (np.tan(1e-10 * np.radians(self.optic.fields.max_field))))

        max_field = np.sqrt(2) / 2
        extent = np.linspace(-max_field, max_field, self.num_points)
        Hx, Hy = np.meshgrid(extent, extent)

        if self.distortion_type == 'f-tan':
            xp = const * np.tan(Hx * np.radians(self.optic.fields.max_field))
            yp = const * np.tan(Hy * np.radians(self.optic.fields.max_field))
        elif self.distortion_type == 'f-theta':
            xp = const * np.tan(Hx * np.radians(self.optic.fields.max_field))
            yp = const * np.tan(Hy * np.radians(self.optic.fields.max_field))
        else:
            raise ValueError('''Distortion type must be "f-tan" or
                                "f-theta"''')

        self.optic.trace_generic(Hx=Hx.flatten(), Hy=Hy.flatten(), Px=0, Py=0,
                                 wavelength=self.wavelength)

        data = {}

        # make real grid square for ease of plotting
        data['xr'] = np.reshape(self.optic.surface_group.x[-1, :],
                                (self.num_points, self.num_points))
        data['yr'] = np.reshape(self.optic.surface_group.y[-1, :],
                                (self.num_points, self.num_points))

        # optical system flips x, so must correct this
        data['xp'] = np.flip(xp)
        data['yp'] = yp

        # Find max distortion
        delta = np.sqrt((data['xp'] - data['xr'])**2 +
                        (data['yp'] - data['yr'])**2)
        rp = np.sqrt(data['xp']**2 + data['yp']**2)

        data['max_distortion'] = np.max(100 * delta / rp)

        return data


class FieldCurvature:

    def __init__(self, optic, wavelengths='all', num_points=128):
        self.optic = optic
        if wavelengths == 'all':
            wavelengths = self.optic.wavelengths.get_wavelengths()
        self.wavelengths = wavelengths
        self.num_points = num_points
        self.data = self._generate_data()

    def view(self, figsize=(8, 5.5)):
        fig, ax = plt.subplots(figsize=figsize)

        field = np.linspace(0, self.optic.fields.max_field, self.num_points)

        for k, wavelength in enumerate(self.wavelengths):
            ax.plot(self.data[k][0], field, f'C{k}', zorder=10,
                    label=f'{wavelength:.4f} µm, Tangential')
            ax.plot(self.data[k][1], field, f'C{k}--', zorder=10,
                    label=f'{wavelength:.4f} µm, Sagittal')

        ax.set_xlabel('Image Plane Delta (mm)')
        ax.set_ylabel('Field')

        ax.set_ylim([0, self.optic.fields.max_field])
        current_xlim = plt.xlim()
        ax.set_xlim([-max(np.abs(current_xlim)), max(np.abs(current_xlim))])
        ax.set_title('Field Curvature')
        plt.axvline(x=0, color='k', linewidth=0.5)
        ax.legend(bbox_to_anchor=(1.05, 0.5), loc='center left')
        fig.tight_layout()
        plt.show()

    def _generate_data(self):
        data = []
        for wavelength in self.wavelengths:
            tangential = self._intersection_parabasal_tangential(wavelength)
            sagittal = self._intersection_parabasal_sagittal(wavelength)

            data.append([tangential, sagittal])

        return data

    def _intersection_parabasal_tangential(self, wavelength, delta=1e-5):
        Hx = np.zeros(2 * self.num_points)
        Hy = np.repeat(np.linspace(0, 1, self.num_points), 2)

        Px = np.zeros(2 * self.num_points)
        Py = np.tile(np.array([-delta, delta]), 128)

        self.optic.trace_generic(Hx, Hy, Px, Py, wavelength=wavelength)

        M1 = self.optic.surface_group.M[-1, ::2]
        N1 = self.optic.surface_group.N[-1, ::2]

        M2 = self.optic.surface_group.M[-1, 1::2]
        N2 = self.optic.surface_group.N[-1, 1::2]

        y01 = self.optic.surface_group.y[-1, ::2]
        z01 = self.optic.surface_group.z[-1, ::2]

        y02 = self.optic.surface_group.y[-1, 1::2]
        z02 = self.optic.surface_group.z[-1, 1::2]

        t1 = (M2*z01 - M2*z02 - N2*y01 + N2*y02) / (M1*N2 - M2*N1)

        return t1 * N1

    def _intersection_parabasal_sagittal(self, wavelength, delta=1e-5):
        Hx = np.zeros(2 * self.num_points)
        Hy = np.repeat(np.linspace(0, 1, self.num_points), 2)

        Px = np.tile(np.array([-delta, delta]), 128)
        Py = np.zeros(2 * self.num_points)

        self.optic.trace_generic(Hx, Hy, Px, Py, wavelength=wavelength)

        L1 = self.optic.surface_group.L[-1, ::2]
        N1 = self.optic.surface_group.N[-1, ::2]

        L2 = self.optic.surface_group.L[-1, 1::2]
        N2 = self.optic.surface_group.N[-1, 1::2]

        x01 = self.optic.surface_group.x[-1, ::2]
        z01 = self.optic.surface_group.z[-1, ::2]

        x02 = self.optic.surface_group.x[-1, 1::2]
        z02 = self.optic.surface_group.z[-1, 1::2]

        t2 = (L2*z01 - L2*z02 - N2*x01 + N2*x02) / (L1*N2 - L2*N1)

        return t2 * N1
