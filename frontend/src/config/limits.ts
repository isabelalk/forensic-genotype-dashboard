// Must match the backend's per-file upload limit.
export const MAX_VCF_UPLOAD_BYTES = 20 * 1024 * 1024;
export const MAX_VCF_UPLOAD_LABEL = '20MB';

export const ACCEPTED_VCF_EXTENSIONS = ['.vcf', '.vcf.gz'] as const;

export const hasAcceptedVcfExtension = (fileName: string): boolean => {
  const lowerName = fileName.toLowerCase();
  return ACCEPTED_VCF_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
};
