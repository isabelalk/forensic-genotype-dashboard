import {
  HiOutlineExclamationCircle,
  HiOutlineInformationCircle,
} from 'react-icons/hi';
import type { ValidationResult } from '../types';

interface ValidationWarningsProps {
  readonly validation: ValidationResult;
}

export const ValidationWarnings = ({ validation }: ValidationWarningsProps) => {
  const hasWarnings = validation.warnings.length > 0 || validation.duplicate_markers.length > 0;

  if (!hasWarnings) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-warning)_42%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))] p-5 animate-slide-up">
      <div className="flex items-start gap-3">
        <HiOutlineExclamationCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-[var(--color-warning)]" />
        <div className="min-w-0 space-y-4">
          <div className="space-y-1">
            <p className="text-lg font-bold text-[var(--color-text)]">Validation warnings</p>
            <p className="text-sm leading-6 text-[var(--color-text-muted)]">These warnings do not block conversion, but they should be reviewed before using the results.</p>
          </div>

          {validation.warnings.length > 0 ? (
            <ul className="space-y-2 text-sm text-[var(--color-text-muted)]">
              {validation.warnings.map((warning) => (
                <li key={warning} className="flex items-start gap-2">
                  <HiOutlineInformationCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-[var(--color-info)]" />
                  <span>{warning}</span>
                </li>
              ))}
            </ul>
          ) : null}

          {validation.duplicate_markers.length > 0 ? (
            <div className="space-y-2">
              <p className="text-sm text-[var(--color-text-muted)]">Duplicate markers detected ({validation.duplicate_markers.length}):</p>
              <div className="flex flex-wrap gap-2">
                {validation.duplicate_markers.map((marker, index) => (
                  <span key={`${index}-${marker}`} className="rounded-lg border border-[color-mix(in_srgb,var(--color-warning)_34%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-warning)_12%,var(--color-card))] px-2 py-1 font-mono text-xs text-[var(--color-text)]">
                    {marker}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
