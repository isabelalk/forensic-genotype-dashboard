import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation } from '@tanstack/react-query';
import {
  HiOutlineCheckCircle,
  HiOutlineCloudUpload,
  HiOutlineDocument,
  HiOutlineExclamationCircle,
  HiOutlineInformationCircle,
} from 'react-icons/hi';
import { vcfApi } from '../api/client';
import type { HirisPlexSResultRow, HirisPlexSResultsResponse } from '../types';

interface PhenotypeCardProps {
  readonly title: string;
  readonly category: string;
  readonly probability: number | null;
  readonly kind: 'eye' | 'hair' | 'skin';
  readonly unavailable?: boolean;
}

interface ResultRowCardProps {
  readonly row: HirisPlexSResultRow;
}

const formatPercent = (probability: number): string => `${(probability * 100).toFixed(1)}%`;
const clampPercent = (probability: number): string => `${Math.min(Math.max(probability * 100, 0), 100).toFixed(1)}%`;

const getPhenotypePalette = (kind: PhenotypeCardProps['kind'], category: string): string => {
  const normalizedCategory = category.toLowerCase();

  if (kind === 'eye') {
    if (normalizedCategory.includes('blue')) return 'from-sky-300 to-blue-600 text-blue-600';
    if (normalizedCategory.includes('intermediate')) return 'from-teal-300 to-amber-500 text-teal-600';
    return 'from-amber-500 to-stone-800 text-amber-700';
  }

  if (kind === 'hair') {
    if (normalizedCategory.includes('blond')) return 'from-yellow-200 to-amber-500 text-amber-600';
    if (normalizedCategory.includes('black')) return 'from-stone-700 to-neutral-950 text-stone-800';
    if (normalizedCategory.includes('red')) return 'from-orange-400 to-red-600 text-orange-600';
    return 'from-amber-700 to-stone-900 text-amber-800';
  }

  if (normalizedCategory.includes('very pale') || normalizedCategory.includes('very fair')) return 'from-rose-100 to-orange-200 text-rose-500';
  if (normalizedCategory.includes('pale') || normalizedCategory.includes('fair')) return 'from-orange-100 to-amber-300 text-orange-500';
  if (normalizedCategory.includes('intermediate')) return 'from-amber-300 to-orange-600 text-amber-700';
  if (normalizedCategory.includes('dark to black') || normalizedCategory.includes('dark-to-black')) return 'from-stone-700 to-stone-950 text-stone-700';
  if (normalizedCategory.includes('dark')) return 'from-orange-800 to-stone-900 text-orange-800';
  return 'from-[var(--color-border)] to-[var(--color-text-muted)] text-[var(--color-text-muted)]';
};

const PhenotypeIllustration = ({ kind, category, unavailable }: Pick<PhenotypeCardProps, 'kind' | 'category' | 'unavailable'>) => {
  const palette = unavailable ? 'from-[var(--color-border)] to-[var(--color-text-muted)] text-[var(--color-text-muted)]' : getPhenotypePalette(kind, category);

  return (
    <div className="relative flex h-20 w-20 flex-shrink-0 items-center justify-center rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] shadow-[var(--shadow-card)]">
      <div className={`absolute inset-2.5 rounded-xl bg-gradient-to-br ${palette} opacity-20`} />
      <svg viewBox="0 0 96 96" className={`relative h-16 w-16 ${palette}`} aria-hidden="true">
        <circle cx="48" cy="42" r="22" fill="currentColor" opacity="0.18" />
        <path d="M22 58c6-18 18-28 26-28s20 10 26 28c-8 8-18 12-26 12S30 66 22 58Z" fill="currentColor" opacity="0.16" />
        {kind === 'eye' ? (
          <>
            <path d="M16 48c10-14 20-21 32-21s22 7 32 21c-10 14-20 21-32 21s-22-7-32-21Z" fill="white" opacity="0.9" />
            <circle cx="48" cy="48" r="15" fill="currentColor" opacity="0.86" />
            <circle cx="48" cy="48" r="6" fill="var(--color-text)" />
            <circle cx="42" cy="42" r="4" fill="white" opacity="0.85" />
          </>
        ) : null}
        {kind === 'hair' ? (
          <>
            <path d="M24 42c2-18 14-29 31-25 13 3 21 14 19 29-8-7-18-8-26-3-8 6-16 5-24-1Z" fill="currentColor" opacity="0.92" />
            <circle cx="48" cy="49" r="18" fill="color-mix(in srgb, var(--color-card) 86%, currentColor)" />
            <path d="M35 72c8 6 18 6 26 0" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="5" opacity="0.7" />
          </>
        ) : null}
        {kind === 'skin' ? (
          <>
            <circle cx="48" cy="43" r="22" fill="currentColor" opacity={unavailable ? '0.22' : '0.74'} />
            <path d="M26 78c5-17 16-25 22-25s17 8 22 25" fill="currentColor" opacity={unavailable ? '0.18' : '0.42'} />
            {unavailable ? <path d="M34 34l28 28M62 34L34 62" stroke="var(--color-card)" strokeLinecap="round" strokeWidth="6" /> : null}
          </>
        ) : null}
      </svg>
    </div>
  );
};

const PhenotypeCard = ({ title, category, probability, kind, unavailable = false }: PhenotypeCardProps) => {
  const palette = unavailable ? 'from-[var(--color-border)] to-[var(--color-text-muted)]' : getPhenotypePalette(kind, category).replace(/ text-.+$/, '');
  const width = probability === null ? '0%' : clampPercent(probability);

  return (
    <article className="glass-hover h-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-4">
      <div className="flex h-full flex-col items-center gap-3 text-center">
        <PhenotypeIllustration kind={kind} category={category} unavailable={unavailable} />
        <div className="flex w-full min-w-0 flex-1 flex-col justify-between space-y-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-text-muted)]">{title}</p>
            <h5 className="mt-1 text-xl font-black tracking-[-0.035em] text-[var(--color-text)]">{category}</h5>
          </div>
          <div className="flex items-center justify-between gap-3 text-xs">
            <span className="text-[var(--color-text-muted)]">Confidence</span>
            <span className="font-mono font-black text-[var(--color-primary)]">{probability === null ? 'Unavailable' : formatPercent(probability)}</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-border)_58%,transparent)]">
            <div className={`probability-bar h-full rounded-full bg-gradient-to-r ${palette} animate-bar-fill`} style={{ width }} />
          </div>
        </div>
      </div>
    </article>
  );
};

const HirisplexResultRowCard = ({ row }: ResultRowCardProps) => {
  const sampleLabel = row.sample_id ?? `Row ${row.row_index}`;
  const skinUnavailable = row.top_predictions.skin_probability === null;

  return (
    <div className="analysis-shell">
      <div className="analysis-core space-y-4 p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[var(--color-success)]">Sample</p>
            <h4 className="text-xl font-black tracking-[-0.04em] text-[var(--color-text)]">{sampleLabel}</h4>
          </div>
          <span className="w-fit rounded-full border border-[color-mix(in_srgb,var(--color-success)_32%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-success)_10%,var(--color-card))] px-3 py-1 font-mono text-xs font-bold text-[var(--color-success)]">
            row {row.row_index}
          </span>
        </div>

        <div className="grid gap-3 lg:grid-cols-3">
          <PhenotypeCard title="Eye Color" category={row.top_predictions.eye_color} probability={row.top_predictions.eye_probability} kind="eye" />
          <PhenotypeCard title="Hair Color" category={row.top_predictions.hair_color} probability={row.top_predictions.hair_probability} kind="hair" />
          <PhenotypeCard title="Skin Color" category={skinUnavailable ? 'Unavailable' : row.top_predictions.skin} probability={row.top_predictions.skin_probability} kind="skin" unavailable={skinUnavailable} />
        </div>

        <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-info)_30%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-info)_10%,var(--color-card))] p-3">
          <p className="flex items-start gap-2 text-sm leading-6 text-[var(--color-text-muted)]">
            <HiOutlineInformationCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-[var(--color-info)]" />
            <span>Skin remains explicitly unavailable when the backend does not return skin probability; no prediction is recalculated in the frontend.</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export const HirisplexSResultsUploadCard = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsedResults, setParsedResults] = useState<HirisPlexSResultsResponse | null>(null);

  const parseMutation = useMutation({
    mutationFn: vcfApi.parseHirisplexSResults,
    onSuccess: (data) => {
      setParsedResults(data);
    },
    onError: (error) => {
      console.error('HIrisPlex-S results parse error:', error);
    },
  });

  const handleDrop = (acceptedFiles: File[]) => {
    const selectedResultFile = acceptedFiles[0];
    if (selectedResultFile) {
      setSelectedFile(selectedResultFile);
      setParsedResults(null);
      parseMutation.reset();
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv'],
      'text/plain': ['.csv'],
    },
    multiple: false,
  });

  const handleParse = () => {
    if (selectedFile) {
      parseMutation.mutate(selectedFile);
    }
  };

  return (
    <div className="analysis-shell min-w-0">
      <div className="analysis-core space-y-4 p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
          <div className="rounded-xl border border-[color-mix(in_srgb,var(--color-success)_32%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-success)_10%,var(--color-card))] p-2.5 text-[var(--color-success)]">
            <HiOutlineCloudUpload className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-black leading-tight tracking-[-0.035em] text-[var(--color-text)] sm:text-xl">HIrisPlex-S Result CSV</h3>
            <p className="text-sm leading-6 text-[var(--color-text-muted)]">Upload the result CSV generated externally by HIrisPlex-S.</p>
          </div>
        </div>

        <div {...getRootProps()} className={`dropzone-surface glass-hover relative cursor-pointer rounded-2xl border-2 border-dashed p-5 ${isDragActive ? 'dropzone-surface--active-success' : 'dropzone-surface--success'}`}>
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center gap-3 text-center">
            <HiOutlineCloudUpload className="h-10 w-10 text-[var(--color-success)]" />
            <div className="space-y-1">
              <p className="font-bold text-[var(--color-text)]">{isDragActive ? 'Drop the CSV here' : 'Drag the HIrisPlex-S result here'}</p>
              <p className="text-sm text-[var(--color-text-muted)]">or click to select a .csv file</p>
            </div>
            <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-1 font-mono text-xs text-[var(--color-text-muted)]">CSV</span>
          </div>
        </div>

        {selectedFile ? (
          <div className="data-surface flex min-w-0 items-center gap-3 rounded-2xl p-4">
            <HiOutlineDocument className="h-7 w-7 flex-shrink-0 text-[var(--color-success)]" />
            <div className="min-w-0">
              <p className="truncate font-bold text-[var(--color-text)]">{selectedFile.name}</p>
              <p className="text-xs text-[var(--color-text-muted)]">{(selectedFile.size / 1024).toFixed(2)} KB</p>
            </div>
          </div>
        ) : null}

        <button onClick={handleParse} disabled={!selectedFile || parseMutation.isPending} className="btn-success w-full px-4 text-base">
          {parseMutation.isPending ? 'Processing CSV...' : 'Read HIrisPlex-S result'}
        </button>

        {parseMutation.error ? (
          <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-error)_42%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-error)_10%,var(--color-card))] p-5 animate-slide-up">
            <div className="flex items-start gap-3">
              <HiOutlineExclamationCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-[var(--color-error)]" />
              <div className="space-y-1">
                <p className="text-lg font-bold text-[var(--color-text)]">Unable to read the CSV.</p>
                <p className="text-sm text-[var(--color-text-muted)]">{parseMutation.error.message}</p>
              </div>
            </div>
          </div>
        ) : null}

        {parsedResults ? (
          <div className="space-y-4 animate-slide-up">
            <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-success)_42%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-success)_10%,var(--color-card))] p-4">
              <div className="flex items-start gap-3">
                <HiOutlineCheckCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-[var(--color-success)]" />
                <div className="space-y-1">
                  <p className="font-bold text-[var(--color-text)]">CSV processed successfully</p>
                  <p className="text-sm text-[var(--color-text-muted)]">{parsedResults.message} ({parsedResults.count} samples)</p>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              {parsedResults.rows.map((row) => <HirisplexResultRowCard key={row.row_index} row={row} />)}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
