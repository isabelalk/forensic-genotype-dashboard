import type { Plex34AncestryRow } from '../types';
import { getSupportedProbabilities, getTopSupportedRegion } from './plex34AncestryRegions';

interface Plex34AncestryMapProps {
  readonly row: Plex34AncestryRow;
}

interface StructureMapLabelProps {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly label: string;
}

const formatPercent = (probability: number): string => `${(probability * 100).toFixed(1)}%`;
const clampWidth = (probability: number): string => `${Math.min(Math.max(probability * 100, 0), 100).toFixed(1)}%`;
const LABEL_HEIGHT = 58;
const LABEL_RADIUS = 20;

const getRegionPathClass = (isActive: boolean): string => (
  isActive
    ? 'fill-[var(--color-primary)]/55 stroke-[var(--color-secondary)] animate-glow drop-shadow-[0_0_18px_var(--color-primary)]'
    : 'fill-[var(--color-card-strong)] stroke-[var(--color-border-strong)] hover:fill-[color-mix(in_srgb,var(--color-primary)_18%,var(--color-card-strong))]'
);

const StructureMapLabel = ({ x, y, width, label }: StructureMapLabelProps) => (
  <g className="structure-map-label" aria-hidden="true">
    <rect x={x - width / 2} y={y - LABEL_HEIGHT / 2} width={width} height={LABEL_HEIGHT} rx={LABEL_RADIUS} className="structure-map-label-bg" />
    <text x={x} y={y} textAnchor="middle" dominantBaseline="middle" className="structure-map-label-text">{label}</text>
  </g>
);

export const Plex34AncestryMap = ({ row }: Plex34AncestryMapProps) => {
  const supportedProbabilities = getSupportedProbabilities(row);
  const topRegion = getTopSupportedRegion(supportedProbabilities);

  return (
    <div className="analysis-shell">
      <div className="analysis-core space-y-4 p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-[var(--color-primary)] sm:tracking-[0.18em]">Primary STRUCTURE</p>
            <h4 className="text-2xl font-black tracking-[-0.04em] text-[var(--color-text)]">{topRegion.label}</h4>
            <p className="text-sm text-[var(--color-text-muted)]">{row.sample_id}</p>
          </div>
          <span className="rounded-full border border-[color-mix(in_srgb,var(--color-secondary)_36%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-secondary)_10%,var(--color-card))] px-3 py-1.5 font-mono text-base font-black text-[var(--color-secondary)]">
            {formatPercent(topRegion.probability)}
          </span>
        </div>

        <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr] lg:items-stretch">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-card-strong)] p-4">
            <div className="mb-4 flex items-center justify-between gap-3">
              <p className="text-sm font-bold text-[var(--color-text)]">STRUCTURE composition</p>
              <p className="text-xs text-[var(--color-text-muted)]">4 populations</p>
            </div>
            <div className="space-y-3">
              {supportedProbabilities.map((region) => {
                const isTopRegion = region.label === topRegion.label;
                return (
                  <div key={region.label} className="space-y-2">
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <span className={isTopRegion ? 'font-black text-[var(--color-primary)]' : 'font-semibold text-[var(--color-text)]'}>{region.label}</span>
                      <span className="font-mono font-bold text-[var(--color-text-muted)]">{formatPercent(region.probability)}</span>
                    </div>
                    <div className="h-2.5 overflow-hidden rounded-full border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-border)_58%,transparent)]">
                      <div className={`probability-bar h-full rounded-full animate-bar-fill ${isTopRegion ? 'bg-[var(--gradient-brand)] shadow-[var(--shadow-glow)]' : 'bg-[color-mix(in_srgb,var(--color-info)_42%,var(--color-border))]'}`} style={{ width: clampWidth(region.probability) }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="relative overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[radial-gradient(circle_at_50%_35%,color-mix(in_srgb,var(--color-primary)_16%,var(--color-card)),var(--color-card-strong)_68%)] p-2 sm:p-3">
            <svg viewBox="0 0 720 360" role="img" aria-label={`STRUCTURE map highlighting ${topRegion.label}`} className="h-64 w-full sm:h-60 lg:h-56">
              <rect width="720" height="360" rx="28" className="fill-transparent" />
              <path d="M80 254c42 24 128 28 178 7" className="stroke-[var(--color-border)]" strokeDasharray="4 10" strokeLinecap="round" strokeWidth="2" fill="none" opacity="0.7" />
              <path d="M256 141c40-26 96-30 138-7" className="stroke-[var(--color-border)]" strokeDasharray="4 10" strokeLinecap="round" strokeWidth="2" fill="none" opacity="0.7" />
              <path d="M395 150c56-22 116-17 168 10" className="stroke-[var(--color-border)]" strokeDasharray="4 10" strokeLinecap="round" strokeWidth="2" fill="none" opacity="0.7" />

              <g aria-label={`Africa ${formatPercent(supportedProbabilities[0]?.probability ?? 0)}`} className="transition-all duration-300">
                <title>Africa {formatPercent(supportedProbabilities[0]?.probability ?? 0)}</title>
                <path d="M286 151c29-20 73-14 98 14 21 24 17 58 1 84-14 22-10 56-36 66-30 12-66-11-76-42-9-28 9-48 1-73-6-20-10-35 12-49Z" className={getRegionPathClass(topRegion.label === 'Africa')} strokeWidth="3" />
                <StructureMapLabel x={278} y={296} width={160} label="Africa" />
              </g>

              <g aria-label={`Europe ${formatPercent(supportedProbabilities[1]?.probability ?? 0)}`} className="transition-all duration-300">
                <title>Europe {formatPercent(supportedProbabilities[1]?.probability ?? 0)}</title>
                <path d="M292 96c26-23 72-25 104-6 29 17 32 47 7 62-20 12-45 5-62 18-19 14-49 10-63-8-14-18-6-45 14-66Z" className={getRegionPathClass(topRegion.label === 'Europe')} strokeWidth="3" />
                <StructureMapLabel x={340} y={72} width={170} label="Europe" />
              </g>

              <g aria-label={`East Asia ${formatPercent(supportedProbabilities[2]?.probability ?? 0)}`} className="transition-all duration-300">
                <title>East Asia {formatPercent(supportedProbabilities[2]?.probability ?? 0)}</title>
                <path d="M462 112c45-34 118-31 159 8 30 29 24 76-14 92-33 14-66-7-95 7-38 18-78-9-84-44-4-24 10-43 34-63Z" className={getRegionPathClass(topRegion.label === 'East Asia')} strokeWidth="3" />
                <StructureMapLabel x={580} y={82} width={230} label="East Asia" />
              </g>

              <g aria-label={`South Asia ${formatPercent(supportedProbabilities[3]?.probability ?? 0)}`} className="transition-all duration-300">
                <title>South Asia {formatPercent(supportedProbabilities[3]?.probability ?? 0)}</title>
                <path d="M429 201c25-16 63-8 81 16 14 18 7 43-13 55-22 14-19 43-45 47-24 4-45-18-42-43 3-25-11-55 19-75Z" className={getRegionPathClass(topRegion.label === 'South Asia')} strokeWidth="3" />
                <StructureMapLabel x={520} y={318} width={250} label="South Asia" />
              </g>
            </svg>
            <div className="pointer-events-none absolute inset-x-6 bottom-4 h-12 rounded-full bg-[color-mix(in_srgb,var(--color-primary)_18%,transparent)] blur-2xl" />
          </div>
        </div>
      </div>
    </div>
  );
};
