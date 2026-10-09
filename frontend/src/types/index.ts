export interface FileUploadResponse {
  readonly file_id: string;
  readonly filename: string;
  readonly size: number;
  readonly message: string;
}

export interface ValidationResult {
  file_id: string;
  filename: string;
  has_ids: boolean;
  duplicate_markers: string[];
  markers_complete: boolean;
  missing_markers: string[];
  missing_genotypes_count: number;
  missing_genotypes: Array<{
    chrom: string;
    pos: number;
    id: string;
    ref: string;
    alt: string;
    genotypes: Record<string, string>; // sample_name -> genotype (e.g., "0/1", "./.")
  }>;
  ref_alt_valid: boolean;
  warnings: string[];
  samples: string[];
  sample_count: number;
}

export interface ConversionRequest {
  file_id: string;
  marker_type: 'hirisplex' | 'plex34';
}

export interface ConversionResponse {
  file_id: string;
  marker_type: 'hirisplex' | 'plex34';
  csv_data: string;
  filename: string;
  row_count: number;
  message: string;
}

export interface Plex34StructureResponse {
  readonly artifact_id: string;
  readonly filenames: readonly string[];
  readonly num_samples: number;
  readonly num_markers: number;
  readonly missing_markers: readonly string[];
  readonly warnings: readonly string[];
  readonly message: string;
}

export interface Plex34StructureOutputResponse {
  readonly sample_lines: readonly string[];
  readonly ancestry_rows: readonly Plex34AncestryRow[];
  readonly count: number;
  readonly message: string;
}

export interface HirisPlexSProbabilities {
  readonly PBlueEye: number;
  readonly PIntermediateEye: number;
  readonly PBrownEye: number;
  readonly PBlondHair: number;
  readonly PBrownHair: number;
  readonly PRedHair: number;
  readonly PBlackHair: number;
  readonly PLightHair: number;
  readonly PDarkHair: number;
  readonly PVeryPaleSkin?: number | null;
  readonly PPaleSkin?: number | null;
  readonly PIntermediateSkin?: number | null;
  readonly PDarkSkin?: number | null;
  readonly PDarktoBlackSkin?: number | null;
}

export type HirisPlexSSkinLabel = 'Very Pale' | 'Pale' | 'Intermediate' | 'Dark' | 'Dark-to-Black' | 'unavailable';

export interface HirisPlexSTopPredictions {
  readonly eye_color: string;
  readonly eye_probability: number;
  readonly hair_color: string;
  readonly hair_probability: number;
  readonly hair_shade: string;
  readonly hair_shade_probability: number;
  readonly skin: HirisPlexSSkinLabel;
  readonly skin_probability: number | null;
}

export interface HirisPlexSResultRow {
  readonly row_index: number;
  readonly sample_id: string | null;
  readonly probabilities: HirisPlexSProbabilities;
  readonly top_predictions: HirisPlexSTopPredictions;
}

export interface HirisPlexSResultsResponse {
  readonly rows: readonly HirisPlexSResultRow[];
  readonly count: number;
  readonly message: string;
}

export interface Plex34ClusterProbability {
  readonly label: string;
  readonly probability: number;
}

export interface Plex34AncestryRow {
  readonly row_index: number;
  readonly sample_id: string;
  readonly probabilities: readonly Plex34ClusterProbability[];
  readonly top_cluster: string;
  readonly confidence: number;
}

export interface MarkersResponse {
  marker_type: string;
  markers: string[];
  count: number;
}
