import {
  HiOutlineCheckCircle,
  HiOutlineDocument,
  HiOutlineDownload,
  HiOutlineExclamationCircle,
  HiOutlineInformationCircle,
  HiOutlineLightningBolt,
} from 'react-icons/hi';
import type { Plex34StructureResponse } from '../types';

interface Plex34StructureCardProps {
  readonly artifact: Plex34StructureResponse | null;
  readonly isGenerating: boolean;
  readonly errorMessage: string | null;
  readonly onGenerate: () => void;
  readonly onDownload: (artifactId: string) => void;
}

export const Plex34StructureCard = ({
  artifact,
  isGenerating,
  errorMessage,
  onGenerate,
  onDownload,
}: Plex34StructureCardProps) => {
  const visibleMissingMarkers = artifact?.missing_markers.slice(0, 8) ?? [];
  const hiddenMissingMarkerCount = artifact
    ? artifact.missing_markers.length - visibleMissingMarkers.length
    : 0;
  const hasArtifactWarnings = artifact
    ? artifact.warnings.length > 0 || artifact.missing_markers.length > 0
    : false;

  return (
    <div className="analysis-shell border-[color-mix(in_srgb,var(--color-primary)_34%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-primary)_9%,var(--color-card))]">
      <div className="analysis-core space-y-4 p-5">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-2.5 shadow-[var(--shadow-glow)]">
            <HiOutlineDocument className="h-6 w-6 text-[var(--color-primary)]" />
          </div>
          <div className="space-y-1">
            <h3 className="text-xl font-black tracking-[-0.04em] text-[var(--color-text)]">PLEX-34 STRUCTURE</h3>
            <p className="text-sm leading-6 text-[var(--color-text-muted)]">Input and configuration package for external analysis.</p>
          </div>
        </div>

        <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-info)_30%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-info)_10%,var(--color-card))] p-3">
          <p className="flex items-start gap-2 text-sm leading-6 text-[var(--color-text-muted)]">
            <HiOutlineInformationCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-[var(--color-info)]" />
            <span>Generates only the STRUCTURE input file, mainparams, and extraparams. It does not run STRUCTURE; after external execution, use the output card to extract sample lines.</span>
          </p>
        </div>

        {!artifact ? (
          <div className="space-y-4">
            <button onClick={onGenerate} disabled={isGenerating} className="btn-primary w-full text-base">
              {isGenerating ? (
                <span className="flex items-center justify-center gap-3">
                  <span className="h-5 w-5 rounded-full border-2 border-white/45 border-t-white motion-safe:animate-spin" />
                  Generating STRUCTURE package...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-3">
                  <HiOutlineLightningBolt className="h-5 w-5" />
                  Generate STRUCTURE input for PLEX-34
                </span>
              )}
            </button>

            {errorMessage ? (
              <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-error)_40%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-error)_10%,var(--color-card))] p-4 animate-slide-up">
                <div className="flex items-start gap-3">
                  <HiOutlineExclamationCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-[var(--color-error)]" />
                  <div className="space-y-1">
                    <p className="font-bold text-[var(--color-text)]">Unable to generate the STRUCTURE package.</p>
                    <p className="text-sm text-[var(--color-text-muted)]">{errorMessage}</p>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="space-y-4 animate-slide-up">
            <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-primary)_40%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-primary)_10%,var(--color-card))] p-4">
              <div className="flex items-start gap-3">
                <HiOutlineCheckCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-[var(--color-primary)]" />
                <div className="space-y-1">
                  <p className="font-bold text-[var(--color-text)]">STRUCTURE package generated successfully</p>
                  <p className="text-sm text-[var(--color-text-muted)]">{artifact.num_samples} samples x {artifact.num_markers} PLEX-34 markers included</p>
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="data-surface rounded-2xl p-3">
                <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Files in package</p>
                <ul className="space-y-2">
                  {artifact.filenames.map((filename) => (
                    <li key={filename} className="flex items-center gap-2 text-sm text-[var(--color-text)]">
                      <HiOutlineDocument className="h-4 w-4 flex-shrink-0 text-[var(--color-info)]" />
                      <span className="truncate font-mono">{filename}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="data-surface rounded-2xl p-3">
                <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Metadata</p>
                <dl className="space-y-2 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <dt className="text-[var(--color-text-muted)]">Samples</dt>
                    <dd className="font-mono font-bold text-[var(--color-info)]">{artifact.num_samples}</dd>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <dt className="text-[var(--color-text-muted)]">Markers</dt>
                    <dd className="font-mono font-bold text-[var(--color-primary)]">{artifact.num_markers}</dd>
                  </div>
                </dl>
              </div>
            </div>

            {hasArtifactWarnings ? (
              <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-warning)_42%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))] p-4">
                <div className="flex items-start gap-3">
                  <HiOutlineExclamationCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-[var(--color-warning)]" />
                  <div className="min-w-0 space-y-3">
                    <p className="font-bold text-[var(--color-text)]">Generated package warnings</p>

                    {artifact.warnings.length > 0 ? (
                      <ul className="space-y-2 text-sm text-[var(--color-text-muted)]">
                        {artifact.warnings.map((warning) => (
                          <li key={warning}>{warning}</li>
                        ))}
                      </ul>
                    ) : null}

                    {visibleMissingMarkers.length > 0 ? (
                      <div className="space-y-2">
                        <p className="text-sm text-[var(--color-text-muted)]">Missing PLEX-34 markers ({artifact.missing_markers.length}):</p>
                        <div className="flex flex-wrap gap-2">
                          {visibleMissingMarkers.map((marker) => (
                            <span key={marker} className="rounded-lg border border-[color-mix(in_srgb,var(--color-warning)_36%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))] px-2 py-1 font-mono text-xs text-[var(--color-text)]">
                              {marker}
                            </span>
                          ))}
                          {hiddenMissingMarkerCount > 0 ? (
                            <span className="rounded-lg border border-[color-mix(in_srgb,var(--color-warning)_36%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))] px-2 py-1 font-mono text-xs text-[var(--color-text)]">
                              +{hiddenMissingMarkerCount}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ) : null}

            <button onClick={() => onDownload(artifact.artifact_id)} className="btn-secondary w-full text-base group">
              <HiOutlineDownload className="h-5 w-5 text-[var(--color-primary)] transition-transform duration-300 group-hover:translate-y-0.5" />
              Download STRUCTURE package (.zip)
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
