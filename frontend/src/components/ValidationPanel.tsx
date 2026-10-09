import { useState, type ReactNode } from 'react';
import {
  HiOutlineCheckCircle,
  HiOutlineDownload,
  HiOutlineExclamationCircle,
  HiOutlineInformationCircle,
  HiOutlineXCircle,
} from 'react-icons/hi';
import { vcfApi } from '../api/client';
import { useVCFStore } from '../store/vcfStore';
import type { ValidationResult } from '../types';
import { ValidationWarnings } from './ValidationWarnings';

interface ValidationPanelProps {
  readonly validation: ValidationResult;
}

interface StatusPanelProps {
  readonly tone: 'success' | 'warning' | 'error' | 'info';
  readonly icon: ReactNode;
  readonly children: ReactNode;
}

const toneClass = {
  success: 'border-[color-mix(in_srgb,var(--color-success)_38%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-success)_10%,var(--color-card))]',
  warning: 'border-[color-mix(in_srgb,var(--color-warning)_42%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))]',
  error: 'border-[color-mix(in_srgb,var(--color-error)_42%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-error)_10%,var(--color-card))]',
  info: 'border-[color-mix(in_srgb,var(--color-info)_34%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-info)_10%,var(--color-card))]',
} as const;

const StatusPanel = ({ tone, icon, children }: StatusPanelProps) => (
  <div className={`rounded-2xl border p-4 ${toneClass[tone]}`}>
    <div className="flex items-start gap-3">{icon}<div className="min-w-0 flex-1">{children}</div></div>
  </div>
);

export const ValidationPanel = ({ validation }: ValidationPanelProps) => {
  const [showMissingGenotypesTable, setShowMissingGenotypesTable] = useState(false);
  const { fileId, continueWithMissingMarkers, continueWithMissingGenotypes, setContinueWithMissingMarkers, setContinueWithMissingGenotypes } = useVCFStore();

  const handleDownloadFullVCF = () => {
    if (fileId) {
      vcfApi.downloadFullVCF(fileId);
    }
  };

  return (
    <div className="space-y-4">
      <StatusPanel tone="success" icon={<HiOutlineCheckCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-success)]" />}>
        <span className="font-bold text-[var(--color-text)]">VCF loaded successfully</span>
      </StatusPanel>

      <ValidationWarnings validation={validation} />

      <StatusPanel tone={validation.has_ids ? 'success' : 'error'} icon={validation.has_ids ? <HiOutlineCheckCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-success)]" /> : <HiOutlineXCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-error)]" />}>
        <span className="font-bold text-[var(--color-text)]">{validation.has_ids ? 'IDs detected in the file.' : 'The VCF file does not have valid IDs in the ID column'}</span>
      </StatusPanel>

      <StatusPanel tone={validation.markers_complete ? 'success' : 'warning'} icon={validation.markers_complete ? <HiOutlineCheckCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-success)]" /> : <HiOutlineExclamationCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-warning)]" />}>
        <div className="space-y-3">
          <span className="font-bold text-[var(--color-text)]">{validation.markers_complete ? 'All required markers are present.' : 'Required markers are missing from the VCF.'}</span>
          {!validation.markers_complete ? (
            <div className="space-y-3">
              <p className="text-sm text-[var(--color-text)]">Missing markers ({validation.missing_markers.length}):</p>
              <div className="data-surface max-h-72 overflow-y-auto rounded-xl p-3">
                <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
                  {validation.missing_markers.map((marker, index) => (
                    <li key={`${index}-${marker}`} className="flex items-center gap-2 rounded-lg border border-[color-mix(in_srgb,var(--color-warning)_30%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))] px-3 py-1.5 transition-colors hover:bg-[color-mix(in_srgb,var(--color-warning)_18%,var(--color-card))]">
                      <span className="h-2 w-2 flex-shrink-0 rounded-full bg-[var(--color-warning)]" />
                      <span className="truncate font-mono text-xs text-[var(--color-text)]">{marker}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <label className="flex cursor-pointer items-center gap-2 group">
                <input type="checkbox" checked={continueWithMissingMarkers} onChange={(event) => setContinueWithMissingMarkers(event.target.checked)} className="h-4 w-4 cursor-pointer" />
                <span className="text-sm text-[var(--color-error)] transition-colors group-hover:brightness-110">Continue anyway</span>
              </label>
            </div>
          ) : null}
        </div>
      </StatusPanel>

      <StatusPanel tone={validation.missing_genotypes_count === 0 ? 'success' : 'warning'} icon={validation.missing_genotypes_count === 0 ? <HiOutlineCheckCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-success)]" /> : <HiOutlineExclamationCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-warning)]" />}>
        <div className="space-y-3">
          <span className="font-bold text-[var(--color-text)]">{validation.missing_genotypes_count === 0 ? 'No missing genotypes detected.' : 'Missing genotypes exist (./. or .|.).'}</span>
          {validation.missing_genotypes_count > 0 ? <p className="text-sm text-[var(--color-text)]">Total missing positions: {validation.missing_genotypes_count}</p> : null}
          <label className="flex cursor-pointer items-center gap-2 group">
            <input type="checkbox" checked={showMissingGenotypesTable} onChange={(event) => setShowMissingGenotypesTable(event.target.checked)} className="h-4 w-4" />
            <span className="text-sm text-[var(--color-info)] transition-colors group-hover:brightness-110">Show complete genotype table?</span>
          </label>

          {showMissingGenotypesTable && validation.missing_genotypes.length > 0 ? (
            <div className="data-surface overflow-hidden rounded-xl">
              <div className="max-h-[32rem] overflow-x-auto overflow-y-auto">
                <table className="w-max min-w-full text-xs">
                  <thead className="sticky top-0 border-b border-[var(--color-border)] bg-[var(--color-card-strong)]">
                    <tr>
                      {['#CHROM', 'POS', 'ID', 'REF', 'ALT'].map((heading) => <th key={heading} className="px-4 py-2 text-left font-bold text-[var(--color-text-muted)]">{heading}</th>)}
                      {validation.samples.map((sample) => <th key={sample} className="px-4 py-2 text-left font-bold text-[var(--color-info)]">{sample}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {validation.missing_genotypes.map((variant, index) => (
                      <tr key={`${index}-${variant.id}`} className="border-t border-[var(--color-border)] transition-colors hover:bg-[color-mix(in_srgb,var(--color-primary)_7%,var(--color-card))]">
                        <td className="px-4 py-2 font-mono text-[var(--color-text)]">{variant.chrom}</td>
                        <td className="px-4 py-2 font-mono text-[var(--color-text)]">{variant.pos}</td>
                        <td className="px-4 py-2 text-[var(--color-warning)]">{variant.id}</td>
                        <td className="px-4 py-2 text-[var(--color-text-muted)]">{variant.ref}</td>
                        <td className="px-4 py-2 text-[var(--color-text-muted)]">{variant.alt}</td>
                        {validation.samples.map((sample) => {
                          const genotype = variant.genotypes[sample];
                          const isMissing = genotype === './.';
                          return <td key={sample} className={`px-4 py-2 text-center font-mono ${isMissing ? 'bg-[color-mix(in_srgb,var(--color-error)_12%,var(--color-card))] font-bold text-[var(--color-error)]' : 'text-[var(--color-text)]'}`}>{genotype}</td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {validation.missing_genotypes_count > 0 ? (
            <label className="flex cursor-pointer items-center gap-2 group">
              <input type="checkbox" checked={continueWithMissingGenotypes} onChange={(event) => setContinueWithMissingGenotypes(event.target.checked)} className="h-4 w-4" />
              <span className="text-sm text-[var(--color-error)] transition-colors group-hover:brightness-110">Continue anyway</span>
            </label>
          ) : null}
        </div>
      </StatusPanel>

      <StatusPanel tone={validation.ref_alt_valid ? 'success' : 'error'} icon={validation.ref_alt_valid ? <HiOutlineCheckCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-success)]" /> : <HiOutlineXCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-error)]" />}>
        <span className="font-bold text-[var(--color-text)]">{validation.ref_alt_valid ? 'REF and ALT are valid.' : 'Variants with invalid REF/ALT exist (not A/T/G/C)'}</span>
      </StatusPanel>

      <StatusPanel tone="info" icon={<HiOutlineInformationCircle className="mt-0.5 h-7 w-7 flex-shrink-0 text-[var(--color-info)]" />}>
        <div className="space-y-3">
          <p className="font-bold text-[var(--color-text)]">Detected samples ({validation.sample_count}):</p>
          <div className="data-surface max-h-72 overflow-y-auto rounded-xl p-3">
            <ul className="flex flex-wrap gap-2">
              {validation.samples.map((sample, index) => <li key={`${index}-${sample}`} className="flex items-center gap-2 rounded-lg border border-[color-mix(in_srgb,var(--color-info)_30%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-info)_10%,var(--color-card))] px-3 py-1.5 transition-colors hover:bg-[color-mix(in_srgb,var(--color-info)_16%,var(--color-card))]"><span className="h-2 w-2 flex-shrink-0 rounded-full bg-[var(--color-info)]" /><span className="text-sm font-medium text-[var(--color-text)]">{sample}</span></li>)}
            </ul>
          </div>
        </div>
      </StatusPanel>

      <button onClick={handleDownloadFullVCF} className="btn-primary w-full py-4 text-base">
        <HiOutlineDownload className="h-5 w-5" />
        <span>Download converted VCF as CSV</span>
      </button>
    </div>
  );
};
