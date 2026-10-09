from pathlib import Path
from typing import Set, List, Dict, Tuple
import pandas as pd
from cyvcf2 import VCF
import io


class VCFProcessor:
    """Service for processing VCF files using cyvcf2"""
    
    def __init__(self, vcf_path: Path):
        self.vcf_path = vcf_path
        self.vcf = None
    
    def __enter__(self):
        """Context manager entry"""
        self.vcf = VCF(str(self.vcf_path))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.vcf:
            self.vcf.close()
    
    def get_samples(self) -> List[str]:
        """Get list of sample names from VCF"""
        if not self.vcf:
            self.vcf = VCF(str(self.vcf_path))
        return list(self.vcf.samples)
    
    def verify_has_ids(self) -> bool:
        """Verify if VCF has valid IDs"""
        if not self.vcf:
            self.vcf = VCF(str(self.vcf_path))
        
        has_valid_id = False
        for variant in self.vcf:
            if variant.ID and variant.ID != '.':
                has_valid_id = True
                break
        
        # Reset VCF reader
        self.vcf = VCF(str(self.vcf_path))
        return has_valid_id
    
    def get_marker_ids(self) -> Set[str]:
        """Get all marker IDs from VCF"""
        if not self.vcf:
            self.vcf = VCF(str(self.vcf_path))
        
        marker_ids = set()
        for variant in self.vcf:
            if variant.ID and variant.ID != '.':
                marker_ids.add(variant.ID)
        
        # Reset VCF reader
        self.vcf = VCF(str(self.vcf_path))
        return marker_ids
    
    def verify_missing_genotypes(self) -> Tuple[int, List[Dict]]:
        """
        Check for missing genotypes (./. or .|.)
        Returns: (count, list of ALL variants with all sample genotypes)
        Each variant in list has structure:
        {
            "chrom": str,
            "pos": int,
            "id": str,
            "ref": str,
            "alt": str,
            "genotypes": {sample_name: genotype_string}
        }
        """
        if not self.vcf:
            self.vcf = VCF(str(self.vcf_path))

        missing_count = 0
        all_variants = []
        samples = self.vcf.samples

        for row_idx, variant in enumerate(self.vcf):
            genotypes_dict = {}

            for sample_idx, genotype in enumerate(variant.genotypes):
                sample_name = samples[sample_idx]
                # genotype is [allele1, allele2, phased]
                if genotype[0] == -1 or genotype[1] == -1:  # -1 means missing
                    genotypes_dict[sample_name] = "./."
                    missing_count += 1
                else:
                    # Format as allele1/allele2
                    genotypes_dict[sample_name] = f"{genotype[0]}/{genotype[1]}"

            # Include ALL variants with their genotypes
            all_variants.append({
                "chrom": variant.CHROM,
                "pos": variant.POS,
                "id": variant.ID or ".",
                "ref": variant.REF,
                "alt": ','.join(variant.ALT) if variant.ALT else '.',
                "genotypes": genotypes_dict
            })

        # Reset VCF reader
        self.vcf = VCF(str(self.vcf_path))
        return missing_count, all_variants
    
    def verify_ref_alt(self) -> bool:
        """Verify REF and ALT contain only valid nucleotides (A/T/G/C)"""
        if not self.vcf:
            self.vcf = VCF(str(self.vcf_path))
        
        valid_nucleotides = {'A', 'T', 'G', 'C'}
        
        for variant in self.vcf:
            # Check REF
            if not all(char in valid_nucleotides for char in variant.REF):
                self.vcf = VCF(str(self.vcf_path))
                return False
            
            # Check ALT alleles
            for alt in variant.ALT:
                if not all(char in valid_nucleotides for char in alt):
                    self.vcf = VCF(str(self.vcf_path))
                    return False
        
        # Reset VCF reader
        self.vcf = VCF(str(self.vcf_path))
        return True
    
    def decode_genotype(self, genotype: List[int], ref: str, alt: List[str]) -> str:
        """
        Convert genotype indices to nucleotide sequence.
        genotype is [allele1, allele2, phased]
        0 = REF, 1+ = ALT index, -1 = missing
        """
        if genotype[0] == -1 or genotype[1] == -1:
            return ""
        
        alleles = [ref] + alt
        
        try:
            allele1 = alleles[genotype[0]]
            allele2 = alleles[genotype[1]]
            return f"{allele1}{allele2}"
        except IndexError:
            return ""
    
    def convert_to_hirisplex(self, required_markers: Set[str]) -> pd.DataFrame:
        """
        Convert VCF to HIrisPlex-S format CSV
        """
        if not self.vcf:
            self.vcf = VCF(str(self.vcf_path))
        
        samples = self.vcf.samples
        rows = []
        
        # Collect data for each variant
        for variant in self.vcf:
            if variant.ID not in required_markers:
                continue
            
            row_data = {"SampleID": variant.ID}
            
            for sample_idx, sample_name in enumerate(samples):
                genotype = variant.genotypes[sample_idx]
                decoded = self.decode_genotype(genotype, variant.REF, variant.ALT)
                row_data[sample_name] = decoded
            
            rows.append(row_data)
        
        # Reset VCF reader
        self.vcf = VCF(str(self.vcf_path))
        
        df = pd.DataFrame(rows)
        
        # Transpose: samples as rows, markers as columns
        if not df.empty:
            df = df.set_index("SampleID").T
            df.index.name = "SampleID"
            df = df.reset_index()
        
        return df
    
    def convert_to_plex34(self, required_markers: Set[str]) -> pd.DataFrame:
        """
        Convert VCF to PLEX-34 format CSV
        Same format as HIrisPlex for now
        """
        return self.convert_to_hirisplex(required_markers)
    
    def get_full_vcf_dataframe(self) -> pd.DataFrame:
        """
        Get full VCF as pandas DataFrame (like Streamlit display)
        """
        if not self.vcf:
            self.vcf = VCF(str(self.vcf_path))
        
        rows = []
        samples = self.vcf.samples
        
        for variant in self.vcf:
            row = {
                '#CHROM': variant.CHROM,
                'POS': variant.POS,
                'ID': variant.ID or '.',
                'REF': variant.REF,
                'ALT': ','.join(variant.ALT) if variant.ALT else '.',
                'QUAL': '.' if variant.QUAL is None else f"{variant.QUAL:.2f}",
                'FILTER': variant.FILTER or '.',
                'INFO': variant.INFO or '.',
                'FORMAT': variant.FORMAT or '.'
            }
            
            # Add sample genotypes
            for sample_idx, sample_name in enumerate(samples):
                genotype_data = variant.genotypes[sample_idx]
                # Format: allele1/allele2:GQ:DP:...
                if genotype_data[0] == -1 or genotype_data[1] == -1:
                    row[sample_name] = './.'
                else:
                    # Get the full format string from the variant
                    gt_str = f"{genotype_data[0]}/{genotype_data[1]}"
                    row[sample_name] = gt_str
            
            rows.append(row)
        
        # Reset VCF reader
        self.vcf = VCF(str(self.vcf_path))

        return pd.DataFrame(rows)
