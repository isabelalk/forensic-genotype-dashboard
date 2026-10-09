interface DataTableRow {
  readonly row: number;
  readonly sample: string;
  readonly position: string;
  readonly id: string;
  readonly ref: string;
  readonly alt: string;
}

interface ParsedDataTableRow {
  readonly chrom: string;
  readonly pos: string;
  readonly id: string;
  readonly ref: string;
  readonly alt: string;
  readonly qual: string;
  readonly filter: string;
  readonly info: string;
  readonly format: string;
  readonly sample: string;
}

interface DataTableProps {
  readonly data: readonly DataTableRow[];
  readonly highlightMissing?: boolean;
}

export const DataTable = ({ data, highlightMissing = false }: DataTableProps) => {
  if (data.length === 0) {
    return (
      <div className="data-surface rounded-2xl p-8 text-center">
        <p className="text-lg text-[var(--color-text-muted)]">No data to display</p>
      </div>
    );
  }

  const parseRow = (item: DataTableRow): ParsedDataTableRow => {
    const [chrom, pos] = item.position.split(':');
    return {
      chrom: chrom || '-',
      pos: pos || '-',
      id: item.id || '-',
      ref: item.ref || '-',
      alt: item.alt || '-',
      qual: '-',
      filter: '-',
      info: '-',
      format: '-',
      sample: item.sample || '-',
    };
  };

  return (
    <div className="data-surface overflow-hidden rounded-2xl shadow-[var(--shadow-card)]">
      <div className="max-h-[32rem] overflow-x-auto">
        <table className="min-w-full divide-y divide-[var(--color-border)]">
          <thead className="sticky top-0 z-10 bg-[var(--color-card-strong)]">
            <tr>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                #CHROM
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                POS
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                ID
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                REF
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                ALT
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                QUAL
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                FILTER
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                INFO
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                FORMAT
              </th>
              <th className="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                Sample
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-border)]">
            {data.map((item, index) => {
              const row = parseRow(item);
              const isMissing = highlightMissing && (row.ref === './.' || row.alt === './.');

              return (
                <tr
                  key={index}
                  className={`transition-colors duration-150 ${
                    isMissing
                      ? 'bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))] hover:bg-[color-mix(in_srgb,var(--color-warning)_18%,var(--color-card))]'
                      : 'hover:bg-[color-mix(in_srgb,var(--color-primary)_7%,var(--color-card))]'
                  }`}
                >
                  <td className="px-4 py-3 font-mono text-sm text-[var(--color-text)]">{row.chrom}</td>
                  <td className="px-4 py-3 font-mono text-sm text-[var(--color-text)]">{row.pos}</td>
                  <td className="px-4 py-3 text-sm font-medium text-[var(--color-info)]">{row.id}</td>
                  <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{row.ref}</td>
                  <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{row.alt}</td>
                  <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{row.qual}</td>
                  <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{row.filter}</td>
                  <td className="max-w-xs truncate px-4 py-3 text-sm text-[var(--color-text-muted)]">{row.info}</td>
                  <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{row.format}</td>
                  <td className="px-4 py-3 text-sm font-medium text-[var(--color-text)]">{row.sample}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
