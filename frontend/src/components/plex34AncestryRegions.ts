import type { Plex34AncestryRow } from '../types';

const SUPPORTED_REGIONS = ['Africa', 'Europe', 'East Asia', 'South Asia'] as const;
type SupportedRegion = typeof SUPPORTED_REGIONS[number];

export interface SupportedRegionProbability {
  readonly label: SupportedRegion;
  readonly probability: number;
}

const CLUSTER_TO_REGION: Record<string, SupportedRegion> = {
  'Cluster 1': 'Africa',
  'Cluster 2': 'Europe',
  'Cluster 3': 'East Asia',
  'Cluster 4': 'South Asia',
  AFR: 'Africa',
  EUR: 'Europe',
  EAS: 'East Asia',
  SAS: 'South Asia',
};

const toSupportedRegion = (label: string): SupportedRegion | null => {
  switch (label) {
    case 'Africa':
    case 'Europe':
    case 'East Asia':
    case 'South Asia':
      return label;
    default:
      return CLUSTER_TO_REGION[label] ?? null;
  }
};

export const getSupportedProbabilities = (row: Plex34AncestryRow): readonly SupportedRegionProbability[] => {
  const probabilitiesByRegion = new Map<SupportedRegion, number>();

  for (const probability of row.probabilities) {
    const region = toSupportedRegion(probability.label);
    if (region) {
      probabilitiesByRegion.set(region, probability.probability);
    }
  }

  return SUPPORTED_REGIONS.map((label) => ({
    label,
    probability: probabilitiesByRegion.get(label) ?? 0,
  }));
};

export const getTopSupportedRegion = (regions: readonly SupportedRegionProbability[]): SupportedRegionProbability => (
  regions.reduce<SupportedRegionProbability>(
    (currentTop, region) => (region.probability > currentTop.probability ? region : currentTop),
    { label: 'Africa', probability: 0 },
  )
);
