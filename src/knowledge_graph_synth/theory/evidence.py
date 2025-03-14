"""Evidence tracking for the knowledge graph synthesis system."""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

import difflib

from ..models import SourceSpan, TextSegment, SegmentCollection
from ..config import settings

logger = logging.getLogger(__name__)


class EvidenceCollector:
    """Collects and tracks evidence for theories and hypotheses.
    
    This class implements methods for finding and tracking evidence that supports
    theories and hypotheses, ensuring that all claims can be traced back to
    source text.
    """
    
    def __init__(self, 
               min_match_length: int = 20,
               match_threshold: float = 0.8):
        """Initialize the evidence collector.
        
        Args:
            min_match_length: Minimum length for text matches
            match_threshold: Threshold for fuzzy matching (0-1)
        """
        self.min_match_length = min_match_length
        self.match_threshold = match_threshold
    
    def find_evidence(self, 
                   claim: str, 
                   collection: SegmentCollection) -> List[SourceSpan]:
        """Find evidence for a claim in the text.
        
        Args:
            claim: Text of the claim to find evidence for
            collection: Segment collection to search
            
        Returns:
            List of source spans containing evidence
        """
        evidence_spans = []
        
        # Clean the claim text
        clean_claim = self._clean_text(claim)
        
        if len(clean_claim) < self.min_match_length:
            # Claim is too short for reliable matching
            return evidence_spans
        
        # Search for the claim in each segment
        for segment_id, segment in collection.segments.items():
            # Try exact match first
            spans = self._find_exact_matches(clean_claim, segment)
            evidence_spans.extend(spans)
            
            if not spans:
                # Try fuzzy matching
                spans = self._find_fuzzy_matches(clean_claim, segment)
                evidence_spans.extend(spans)
        
        return evidence_spans
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better matching.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', text)
        
        # Remove quotes
        clean = clean.replace('"', '').replace('"', '').replace('"', '')
        
        # Remove parenthetical comments
        clean = re.sub(r'\([^)]*\)', '', clean)
        
        # Remove square bracket citations
        clean = re.sub(r'\[[^\]]*\]', '', clean)
        
        return clean.strip()
    
    def _find_exact_matches(self, 
                        claim: str, 
                        segment: TextSegment) -> List[SourceSpan]:
        """Find exact matches for a claim in a segment.
        
        Args:
            claim: Text to find
            segment: Text segment to search in
            
        Returns:
            List of source spans containing matches
        """
        spans = []
        segment_text = segment.text
        claim_lower = claim.lower()
        segment_lower = segment_text.lower()
        
        # Find all occurrences of the claim text in the segment
        start_pos = 0
        while start_pos < len(segment_lower):
            pos = segment_lower.find(claim_lower, start_pos)
            
            if pos == -1:
                break
            
            # Create a source span for this match
            span = SourceSpan(
                document_id=segment.document_id,
                segment_id=str(segment.id),
                start=pos,
                end=pos + len(claim),
                text=segment_text[pos:pos + len(claim)]
            )
            
            spans.append(span)
            
            # Move to the next position
            start_pos = pos + 1
        
        return spans
    
    def _find_fuzzy_matches(self, 
                        claim: str, 
                        segment: TextSegment) -> List[SourceSpan]:
        """Find fuzzy matches for a claim in a segment.
        
        Args:
            claim: Text to find
            segment: Text segment to search in
            
        Returns:
            List of source spans containing matches
        """
        spans = []
        segment_text = segment.text
        
        # Only attempt fuzzy matching on shorter segments to limit processing time
        if len(segment_text) > 10000:
            return spans
        
        # Split the segment into sentences
        sentences = re.split(r'(?<=[.!?])\s+', segment_text)
        
        for sentence in sentences:
            if len(sentence) < self.min_match_length:
                continue
            
            # Calculate similarity ratio
            similarity = difflib.SequenceMatcher(None, claim.lower(), sentence.lower()).ratio()
            
            if similarity >= self.match_threshold:
                # Find the position of this sentence in the segment
                pos = segment_text.find(sentence)
                
                if pos != -1:
                    # Create a source span for this match
                    span = SourceSpan(
                        document_id=segment.document_id,
                        segment_id=str(segment.id),
                        start=pos,
                        end=pos + len(sentence),
                        text=sentence
                    )
                    
                    spans.append(span)
        
        return spans
    
    def collect_evidence(self, 
                      claims: List[str],
                      collection: SegmentCollection) -> Dict[str, List[SourceSpan]]:
        """Collect evidence for multiple claims.
        
        Args:
            claims: List of claim texts
            collection: Segment collection to search
            
        Returns:
            Dictionary mapping claims to evidence spans
        """
        evidence = {}
        
        for claim in claims:
            spans = self.find_evidence(claim, collection)
            evidence[claim] = spans
        
        return evidence
    
    def format_evidence_citation(self, span: SourceSpan) -> str:
        """Format a source span as a citation.
        
        Args:
            span: Source span to format
            
        Returns:
            Formatted citation string
        """
        doc_part = f"document {span.document_id}" if span.document_id else "unknown document"
        seg_part = f", segment {span.segment_id}" if span.segment_id else ""
        pos_part = f", positions {span.start}-{span.end}"
        
        citation = f"[{doc_part}{seg_part}{pos_part}]"
        
        # Add a quote of the text
        max_quote_length = 100
        if span.text:
            text = span.text
            if len(text) > max_quote_length:
                text = text[:max_quote_length - 3] + "..."
            
            citation += f": \"{text}\""
        
        return citation