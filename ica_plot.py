import mne
import copy
import matplotlib as plt
import numpy as np
from mne.viz import _get_plot_ch_type 
from mne.viz.utils import _setup_cmap, _prepare_sensor_names, _prepare_trellis, _setup_vmin_vmax, plt_show
from mne._fiff.pick import _picks_to_idx
from mne.viz.topomap import _prepare_topomap_plot, _make_head_outlines, plot_topomap, _add_colorbar, _hide_frame
from matplotlib.pyplot import Axes

from mne.channels.layout import _merge_ch_data
from mne.epochs import BaseEpochs
from mne.io import BaseRaw



# straight from defaults
_BORDER_DEFAULT = "mean"
_INTERPOLATION_DEFAULT = "cubic"
_EXTRAPOLATE_DEFAULT = "auto"


def custome_ica_plot(
    ica,
    ICA_remove_inds_list,
    feedback = False,
    deselect =  False,
    picks=None,
    ch_type=None,
    *,
    inst=None,
    plot_std=True,
    reject="auto",
    sensors=True,
    show_names=False,
    contours=6,
    outlines="head",
    sphere=None,
    image_interp= _INTERPOLATION_DEFAULT,
    extrapolate=_EXTRAPOLATE_DEFAULT,
    border=_BORDER_DEFAULT,
    res=64,
    size=1,
    cmap="RdBu_r",
    vlim=(None, None),
    cnorm=None,
    colorbar=False,
    cbar_fmt="%3.2f",
    axes=None,
    title=None,
    nrows="auto",
    ncols="auto",
    show=True,
    image_args=None,
    psd_args=None,
    verbose=None,
):
    """Project mixing matrix on interpolated sensor topography.

    Parameters
    ----------
    ica : instance of mne.preprocessing.ICA
        The ICA solution.
    %(picks_ica)s
    %(ch_type_topomap)s
    inst : Raw | Epochs | None
        To be able to see component properties after clicking on component
        topomap you need to pass relevant data - instances of Raw or Epochs
        (for example the data that ICA was trained on). This takes effect
        only when running matplotlib in interactive mode.
    plot_std : bool | float
        Whether to plot standard deviation in ERP/ERF and spectrum plots.
        Defaults to True, which plots one standard deviation above/below.
        If set to float allows to control how many standard deviations are
        plotted. For example 2.5 will plot 2.5 standard deviation above/below.
    reject : ``'auto'`` | dict | None
        Allows to specify rejection parameters used to drop epochs
        (or segments if continuous signal is passed as inst).
        If None, no rejection is applied. The default is 'auto',
        which applies the rejection parameters used when fitting
        the ICA object.
    %(sensors_topomap)s
    %(show_names_topomap)s
    %(contours_topomap)s
    %(outlines_topomap)s
    %(sphere_topomap_auto)s
    %(image_interp_topomap)s
    %(extrapolate_topomap)s

        .. versionadded:: 1.3
    %(border_topomap)s

        .. versionadded:: 1.3
    %(res_topomap)s
    %(size_topomap)s

        .. versionadded:: 1.3
    %(cmap_topomap)s
    %(vlim_plot_topomap)s

        .. versionadded:: 1.3
    %(cnorm)s

        .. versionadded:: 1.3
    %(colorbar_topomap)s
    %(cbar_fmt_topomap)s
    axes : Axes | array of Axes | None
        The subplot(s) to plot to. Either a single Axes or an iterable of Axes
        if more than one subplot is needed. The number of subplots must match
        the number of selected components. If None, new figures will be created
        with the number of subplots per figure controlled by ``nrows`` and
        ``ncols``.
    title : str | None
        The title of the generated figure. If ``None`` (default) and
        ``axes=None``, a default title of "ICA Components" will be used.
    %(nrows_ncols_ica_components)s

        .. versionadded:: 1.3
    %(show)s
    image_args : dict | None
        Dictionary of arguments to pass to :func:`~mne.viz.plot_epochs_image`
        in interactive mode. Ignored if ``inst`` is not supplied. If ``None``,
        nothing is passed. Defaults to ``None``.
    psd_args : dict | None
        Dictionary of arguments to pass to :meth:`~mne.Epochs.compute_psd` in
        interactive  mode. Ignored if ``inst`` is not supplied. If ``None``,
        nothing is passed. Defaults to ``None``.
    %(verbose)s

    Returns
    -------
    fig : instance of matplotlib.figure.Figure | list of matplotlib.figure.Figure
        The figure object(s).

    Notes
    -----
    When run in interactive mode, ``plot_ica_components`` allows to reject
    components by clicking on their title label. The state of each component
    is indicated by its label color (gray: rejected; black: retained). It is
    also possible to open component properties by clicking on the component
    topomap (this option is only available when the ``inst`` argument is
    supplied).
    """  # noqa E501



    if ica.info is None:
        raise RuntimeError(
            "The ICA's measurement info is missing. Please "
            "fit the ICA or add the corresponding info object."
        )

    # for backward compat, nrow='auto' ncol='auto' should yield 4 rows 5 cols
    # and create multiple figures if more than 20 components requested
    if nrows == "auto" and ncols == "auto":
        ncols = 5
        max_subplots = 20
    elif nrows == "auto" or ncols == "auto":
        # user provided incomplete row/col spec; put all in one figure
        max_subplots = ica.n_components_
    else:
        max_subplots = nrows * ncols

    # handle ch_type=None
    ch_type = _get_plot_ch_type(ica, ch_type)

    figs = []
    if picks is None:
        cut_points = range(max_subplots, ica.n_components_, max_subplots)
        pick_groups = np.split(range(ica.n_components_), cut_points)
    else:
        pick_groups = [_picks_to_idx(ica.n_components_, picks, picks_on="components")]

    axes = axes.flatten() if isinstance(axes, np.ndarray) else axes
    for k, picks in enumerate(pick_groups):
        try:  # either an iterable, 1D numpy array or others
            _axes = axes[k * max_subplots : (k + 1) * max_subplots]
        except TypeError:  # None or Axes
            _axes = axes

        (
            data_picks,
            pos,
            merge_channels,
            names,
            ch_type,
            sphere,
            clip_origin,
        ) = _prepare_topomap_plot(ica, ch_type, sphere=sphere)

        cmap = _setup_cmap(cmap, n_axes=len(picks))
        names = _prepare_sensor_names(names, show_names)
        outlines = _make_head_outlines(sphere, pos, outlines, clip_origin)

        data = np.dot(
            ica.mixing_matrix_[:, picks].T, ica.pca_components_[: ica.n_components_]
        )
        data = np.atleast_2d(data)
        data = data[:, data_picks]

        if title is None:
            title = "ICA components"
        user_passed_axes = _axes is not None
        if not user_passed_axes:
            fig, _axes, _, _ = _prepare_trellis(len(data), ncols=ncols, nrows=nrows)
            fig.suptitle(title)
        else:
            _axes = [_axes] if isinstance(_axes, Axes) else _axes
            fig = _axes[0].get_figure()

        subplot_titles = list()
        for ii, data_, ax in zip(picks, data, _axes):
            kwargs = dict(color="gray") if ii in ica.exclude else dict()
            comp_title = ica._ica_names[ii]
            if len(set(ica.get_channel_types())) > 1:
                comp_title += f" ({ch_type})"
        ##########
            title_text = ax.set_title(comp_title, fontsize=12, **kwargs)
            title_text.set_picker(True)
            subplot_titles.append(title_text)
        #####################
            if merge_channels:
                data_, names_ = _merge_ch_data(data_, ch_type, copy.copy(names))
            # ↓↓↓ NOTE: we intentionally use the default norm=False here, so that
            # ↓↓↓ we get vlims that are symmetric-about-zero, even if the data for
            # ↓↓↓ a given component happens to be one-sided.
            _vlim = _setup_vmin_vmax(data_, *vlim)
            im = plot_topomap(
                data_.flatten(),
                pos,
                ch_type=ch_type,
                sensors=sensors,
                names=names,
                contours=contours,
                outlines=outlines,
                sphere=sphere,
                image_interp=image_interp,
                extrapolate=extrapolate,
                border=border,
                res=res,
                size=size,
                cmap=cmap[0],
                vlim=_vlim,
                cnorm=cnorm,
                axes=ax,
                show=False,
            )[0]

            im.axes.set_label(ica._ica_names[ii])
            if colorbar:
                cbar, cax = _add_colorbar(
                    ax,
                    im,
                    cmap,
                    title="AU",
                    format_=cbar_fmt,
                    kind="ica_comp_topomap",
                    ch_type=ch_type,
                )
                cbar.ax.tick_params(labelsize=12)
                cbar.set_ticks(_vlim)
            _hide_frame(ax)
        del pos
        fig.canvas.draw()

        # add title selection interactivity
        def onclick_title(event, ica=ica, titles=subplot_titles, fig=fig):
            # check if any title was pressed
            title_pressed = None
            for title in titles:
                if title.contains(event)[0]:
                    title_pressed = title
                    break
            # title was pressed -> identify the IC
            if title_pressed is not None:
                label = title_pressed.get_text()
                ic = int(label.split(" ")[0][-3:])
                # add or remove IC from exclude depending on current state
                if ic in ica.exclude:
                    if deselect:
                        ica.exclude.remove(ic)
                        title_pressed.set_color("k")
                        message = f"Unmarked component {ic} as bad."
                        color = 'green' if ic not in ICA_remove_inds_list else 'red'
                    else:
                        message = None
                        color = None
                else:
                    ica.exclude.append(ic)
                    title_pressed.set_color("gray")
                    message = f"Marked component {ic} as bad."
                    color = 'green' if ic in ICA_remove_inds_list else 'red'
                if feedback:
                    if hasattr(fig, '_feedback_text'):
                        fig._feedback_text.remove()
                    # Add new feedback text
                    fig._feedback_text = fig.text(
                        0.5, 0.95, message, ha='center', va='center', color=color, fontsize=14
                    )
                fig.canvas.draw()

        fig.canvas.mpl_connect("button_press_event", onclick_title)

        # add plot_properties interactivity only if inst was passed
        #if isinstance(inst, BaseRaw | BaseEpochs):
        if isinstance(inst,(BaseRaw, BaseEpochs)):
            topomap_args = dict(
                sensors=sensors,
                contours=contours,
                outlines=outlines,
                sphere=sphere,
                image_interp=image_interp,
                extrapolate=extrapolate,
                border=border,
                res=res,
                cmap=cmap[0],
                vmin=vlim[0],
                vmax=vlim[1],
            )

            def onclick_topo(event, ica=ica, inst=inst):
                # check which component to plot
                if event.inaxes is not None:
                    label = event.inaxes.get_label()
                    if label.startswith("ICA"):
                        ic = int(label.split(" ")[0][-3:])
                        ica.plot_properties(
                            inst,
                            picks=ic,
                            show=True,
                            plot_std=plot_std,
                            topomap_args=topomap_args,
                            image_args=image_args,
                            psd_args=psd_args,
                            reject=reject,
                        )

            fig.canvas.mpl_connect("button_press_event", onclick_topo)
        figs.append(fig)

    plt_show(show)
    return figs[0] if len(figs) == 1 else figs
