import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  HiOutlineCheckCircle,
  HiOutlineDocument,
  HiOutlineDownload,
  HiOutlineInformationCircle,
  HiOutlineLightningBolt,
} from 'react-icons/hi';
import { vcfApi } from '../api/client';
import { useVCFStore } from '../store/vcfStore';
import type { ConversionResponse, Plex34StructureResponse } from '../types';
import { Plex34StructureCard } from './Plex34StructureCard';

type MarkerConversion = 'hirisplex' | 'plex34';
type ConversionTone = 'success' | 'brand';

interface ConversionCardProps {
  readonly title: string;
  readonly tone: ConversionTone;
  readonly isPending: boolean;
  readonly isComplete: boolean;
  readonly pendingText: string;
  readonly actionText: string;
  readonly successTitle: string;
  readonly successDetail: string;
  readonly downloadText: string;
  readonly infoText: string;
  readonly onConvert: () => void;
  readonly onDownload: () => void;
}

const getToneTokens = (tone: ConversionTone) => {
  if (tone === 'success') {
    return {
      accent: 'var(--color-success)',
      panel: 'bg-[color-mix(in_srgb,var(--color-success)_10%,var(--color-card))] border-[color-mix(in_srgb,var(--color-success)_34%,var(--color-border))]',
      button: 'btn-success',
      icon: 'text-[var(--color-success)]',
      shadow: 'shadow-[var(--shadow-success)]',
    };
  }

  return {
    accent: 'var(--color-primary)',
    panel: 'bg-[color-mix(in_srgb,var(--color-primary)_10%,var(--color-card))] border-[color-mix(in_srgb,var(--color-primary)_34%,var(--color-border))]',
    button: 'btn-primary',
    icon: 'text-[var(--color-primary)]',
    shadow: 'shadow-[var(--shadow-glow)]',
  };
};

const ConversionCard = ({
  title,
  tone,
  isPending,
  isComplete,
  pendingText,
  actionText,
  successTitle,
  successDetail,
  downloadText,
  infoText,
  onConvert,
  onDownload,
}: ConversionCardProps) => {
  const toneTokens = getToneTokens(tone);

  return (
    <div className={`analysis-shell ${toneTokens.panel}`}>
      <div className="analysis-core space-y-4 p-5">
        <div className="flex items-center gap-3">
          <div className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-2.5 ${toneTokens.shadow}`}>
            <HiOutlineDocument className={`h-6 w-6 ${toneTokens.icon}`} />
          </div>
          <h3 className="text-xl font-black tracking-[-0.04em] text-[var(--color-text)]">{title}</h3>
        </div>

        {!isComplete ? (
          <button onClick={onConvert} disabled={isPending} className={`${toneTokens.button} w-full text-base`}>
            {isPending ? (
              <span className="flex items-center justify-center gap-3">
                <span className="h-5 w-5 rounded-full border-2 border-white/45 border-t-white motion-safe:animate-spin" />
                {pendingText}
              </span>
            ) : (
              <span className="flex items-center justify-center gap-3">
                <HiOutlineLightningBolt className="h-6 w-6" />
                {actionText}
              </span>
            )}
          </button>
        ) : (
          <div className="space-y-4 animate-slide-up">
            <div className={`rounded-2xl border p-4 ${toneTokens.panel}`}>
              <div className="flex items-start gap-3">
                <HiOutlineCheckCircle className={`mt-0.5 h-6 w-6 flex-shrink-0 ${toneTokens.icon}`} />
                <div>
                  <p className="mb-1 font-bold text-[var(--color-text)]">{successTitle}</p>
                  <p className="text-sm text-[var(--color-text-muted)]">{successDetail}</p>
                </div>
              </div>
            </div>

            <button onClick={onDownload} className="btn-secondary w-full text-base group">
              <HiOutlineDownload className={`h-5 w-5 ${toneTokens.icon} transition-transform duration-300 group-hover:translate-y-0.5`} />
              {downloadText}
            </button>

            <div className="rounded-2xl border border-[color-mix(in_srgb,var(--color-info)_30%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-info)_10%,var(--color-card))] p-3">
              <p className="flex items-start gap-2 text-sm leading-6 text-[var(--color-text-muted)]">
                <HiOutlineInformationCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-[var(--color-info)]" />
                <span>{infoText}</span>
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const ConversionSection = () => {
  const { fileId, validationResult } = useVCFStore();
  const [activeConversion, setActiveConversion] = useState<MarkerConversion | null>(null);
  const [conversionResults, setConversionResults] = useState<{
    hirisplex?: ConversionResponse;
    plex34?: ConversionResponse;
  }>({});
  const [plex34StructureResult, setPlex34StructureResult] = useState<Plex34StructureResponse | null>(null);

  const convertMutation = useMutation({
    mutationFn: vcfApi.convertFile,
    onSuccess: (data) => {
      setConversionResults(prev => ({
        ...prev,
        [data.marker_type]: data,
      }));
      setActiveConversion(null);
    },
    onError: (error) => {
      console.error('Conversion error:', error);
      setActiveConversion(null);
    },
  });

  const handleConvert = (markerType: MarkerConversion) => {
    if (!fileId) return;

    setActiveConversion(markerType);
    convertMutation.mutate({
      file_id: fileId,
      marker_type: markerType,
    });
  };

  const plex34StructureMutation = useMutation({
    mutationFn: vcfApi.generatePlex34StructureInput,
    onSuccess: (data) => {
      setPlex34StructureResult(data);
    },
    onError: (error) => {
      console.error('Plex34 STRUCTURE generation error:', error);
    },
  });

  const handleGeneratePlex34Structure = () => {
    if (!fileId) return;

    plex34StructureMutation.mutate(fileId);
  };

  const handleDownloadPlex34Structure = (artifactId: string) => {
    vcfApi.downloadPlex34StructureInput(artifactId);
  };

  const handleDownload = (markerType: MarkerConversion) => {
    if (!fileId) return;
    vcfApi.downloadFile(fileId, markerType);
  };

  const canConvert = validationResult &&
    validationResult.has_ids &&
    validationResult.ref_alt_valid;

  if (!canConvert) {
    return null;
  }

  return (
    <div className="space-y-5">
      <ConversionCard
        title="HIrisPlex-S"
        tone="success"
        isPending={convertMutation.isPending && activeConversion === 'hirisplex'}
        isComplete={Boolean(conversionResults.hirisplex)}
        pendingText="Processing..."
        actionText="Process VCF for HIrisPlex-S"
        successTitle="File generated successfully"
        successDetail="Ready for download and use on the HIrisPlex-S website"
        downloadText="Download HIrisPlex-S file"
        infoText="You can now upload this file to the HIrisPlex-S website to obtain phenotype prediction."
        onConvert={() => handleConvert('hirisplex')}
        onDownload={() => handleDownload('hirisplex')}
      />

      <ConversionCard
        title="PLEX-34"
        tone="brand"
        isPending={convertMutation.isPending && activeConversion === 'plex34'}
        isComplete={Boolean(conversionResults.plex34)}
        pendingText="Processing..."
        actionText="Process VCF for PLEX-34"
        successTitle="PLEX-34 file generated successfully"
        successDetail="Forensic file ready for analysis"
        downloadText="Download PLEX-34 file"
        infoText="This file contains only markers from the PLEX-34 forensic panel."
        onConvert={() => handleConvert('plex34')}
        onDownload={() => handleDownload('plex34')}
      />

      <Plex34StructureCard
        artifact={plex34StructureResult}
        isGenerating={plex34StructureMutation.isPending}
        errorMessage={plex34StructureMutation.error?.message ?? null}
        onGenerate={handleGeneratePlex34Structure}
        onDownload={handleDownloadPlex34Structure}
      />
    </div>
  );
};
