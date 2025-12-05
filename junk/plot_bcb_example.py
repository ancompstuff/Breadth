def plot_bcb_with_extrapolation(df, metadata, ax, plot_index):
    """
    Plot SELIC and IPCA with dashed lines for extrapolated portions.

    Parameters
    ----------
    df : pd.DataFrame
        From get_idx1_idx2, with columns SELIC, IPCA
    metadata : dict
        Contains 'selic_extrapolated_from', 'ipca_extrapolated_from'
    ax : matplotlib axis
    plot_index : range or array
        Numeric index for x-axis (e.g., range(len(df)))
    """

    # Plot SELIC
    if metadata['selic_extrapolated_from'] is None:
        # All real data
        ax.plot(plot_index, df['SELIC'], color='blue', linewidth=2, label='SELIC')
    else:
        # Split into real and extrapolated
        cutoff_date = metadata['selic_extrapolated_from']
        real_mask = df.index <= cutoff_date
        extrap_mask = df.index >= cutoff_date

        ax.plot(plot_index[real_mask], df.loc[real_mask, 'SELIC'],
                color='blue', linewidth=2, label='SELIC')
        ax.plot(plot_index[extrap_mask], df.loc[extrap_mask, 'SELIC'],
                color='blue', linewidth=2, linestyle='--', alpha=0.5,
                label='SELIC (extrapolado)')

    # Plot IPCA
    if metadata['ipca_extrapolated_from'] is None:
        # All real data
        ax.plot(plot_index, df['IPCA'], color='red', linewidth=2, label='IPCA')
    else:
        # Split into real and extrapolated
        cutoff_date = metadata['ipca_extrapolated_from']
        real_mask = df.index <= cutoff_date
        extrap_mask = df.index >= cutoff_date

        ax.plot(plot_index[real_mask], df.loc[real_mask, 'IPCA'],
                color='red', linewidth=2, label='IPCA')
        ax.plot(plot_index[extrap_mask], df.loc[extrap_mask, 'IPCA'],
                color='red', linewidth=2, linestyle='--', alpha=0.5,
                label='IPCA (extrapolado)')

    ax.legend(loc='best', fontsize=9)
    ax.set_ylabel('Taxa (%)', fontsize=10)
    ax.grid(True, alpha=0.3)