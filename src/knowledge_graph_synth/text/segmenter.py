"""Text segmentation for the knowledge graph synthesis system."""

import re
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4

from ..models.segment import TextSegment, SegmentCollection
from ..config import settings


class TextSegmenter:
    """Segments text into processable chunks.
    
    This class breaks down large text documents into smaller segments for processing,
    preserving hierarchical relationships between segments and maintaining position
    information for provenance tracking.
    """
    
    def __init__(self, 
                max_segment_length: int = settings.MAX_SEGMENT_LENGTH,
                max_segment_overlap: int = settings.MAX_SEGMENT_OVERLAP):
        """Initialize the text segmenter.
        
        Args:
            max_segment_length: Maximum characters per segment
            max_segment_overlap: Overlap between segments in characters
        """
        self.max_segment_length = max_segment_length
        self.max_segment_overlap = max_segment_overlap
        
        # Regex patterns for segmentation
        self.paragraph_pattern = re.compile(r'\n\s*\n')
        self.section_header_pattern = re.compile(r'\n[A-Z][A-Z0-9 ,.;:&\'-]*\n')
    
    def segment(self, collection: SegmentCollection) -> SegmentCollection:
        """Segment a SegmentCollection.
        
        Args:
            collection: SegmentCollection to segment
            
        Returns:
            SegmentCollection with added segments
        """
        # Get root segments to process
        root_segments = collection.get_root_segments()
        
        # Process each root segment
        for root in root_segments:
            # If text starts with WEBVTT, treat as transcript with special segmentation
            if root.text and root.text.startswith("WEBVTT"):
                transcript_segments = self._segment_transcript(root)
                for segment in transcript_segments:
                    collection.add_segment(segment)
            else:
                # Standard paragraph-based segmentation for normal text
                paragraph_segments = self._segment_by_paragraphs(root)
                
                for paragraph in paragraph_segments:
                    # If paragraph is too long, split it further
                    if paragraph.length > self.max_segment_length:
                        sentence_segments = self._segment_by_sentences(paragraph)
                        for sentence in sentence_segments:
                            collection.add_segment(sentence)
                    else:
                        collection.add_segment(paragraph)
        
        return collection
        
    def _segment_transcript(self, segment: TextSegment) -> List[TextSegment]:
        """Segment a transcript (WEBVTT format) by conversation topics.
        
        Args:
            segment: Text segment containing transcript
            
        Returns:
            List of segmented transcript segments by topic
        """
        text = segment.text
        # Split by timestamp lines
        lines = text.split('\n')
        
        # Collect utterances (speaker turns)
        utterances = []
        current_utterance = ""
        timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}')
        
        for line in lines:
            if timestamp_pattern.match(line):
                # New timestamp, if we have an utterance, add it
                if current_utterance.strip():
                    utterances.append(current_utterance.strip())
                    current_utterance = ""
            elif line.strip() and not line.startswith("WEBVTT"):
                current_utterance += line + " "
        
        # Add the last utterance if any
        if current_utterance.strip():
            utterances.append(current_utterance.strip())
        
        # Group utterances into topic-based segments
        # Using a simple approach of grouping every 5-10 utterances as a "topic"
        # In a real system, this could use more sophisticated topic detection
        topic_segments = []
        current_topic = ""
        num_topics = min(20, max(5, len(utterances) // 25))  # Aim for about 5-20 topics total
        utterances_per_topic = max(5, len(utterances) // num_topics)  # At least 5 utterances per topic
        
        for i, utterance in enumerate(utterances):
            current_topic += utterance + "\n\n"
            
            # When we reach the desired number of utterances or the end, create a segment
            if (i + 1) % utterances_per_topic == 0 or i == len(utterances) - 1:
                if current_topic.strip():
                    # Важно: для транскриптов не устанавливаем позиции start_position и end_position,
                    # так как они имеют другую структуру и нам не нужны точные позиции
                    topic = TextSegment(
                        document_id=segment.document_id,
                        text=current_topic.strip(),
                        language=segment.language,
                        parent_id=segment.id,
                        metadata={
                            "segment_type": "transcript_topic",
                            "parent_segment": str(segment.id),
                            "topic_number": len(topic_segments) + 1
                        }
                    )
                    topic_segments.append(topic)
                    current_topic = ""
        
        return topic_segments
    
    def _segment_by_paragraphs(self, segment: TextSegment) -> List[TextSegment]:
        """Split a segment into paragraphs.
        
        Args:
            segment: Text segment to split
            
        Returns:
            List of paragraph segments
        """
        text = segment.text
        matches = list(self.paragraph_pattern.finditer(text))
        
        # If no paragraph breaks or only one paragraph, return the segment as is
        if not matches:
            return [segment]
        
        # Create paragraph segments
        paragraphs = []
        start_idx = 0
        
        for match in matches:
            if start_idx == match.start():
                # Skip empty paragraphs
                start_idx = match.end()
                continue
            
            # Extract paragraph text
            paragraph_text = text[start_idx:match.start()]
            
            # Create paragraph segment
            start_pos = None
            end_pos = None
            
            # Рассчитываем позиции только если родительский сегмент имеет действительные позиции
            if segment.start_position is not None:
                start_pos = segment.start_position + start_idx
                end_pos = segment.start_position + match.start()
                
            paragraph = TextSegment(
                document_id=segment.document_id,
                text=paragraph_text,
                start_position=start_pos,
                end_position=end_pos,
                language=segment.language,
                parent_id=segment.id,
                metadata={
                    "segment_type": "paragraph",
                    "parent_segment": str(segment.id)
                }
            )
            
            paragraphs.append(paragraph)
            start_idx = match.end()
        
        # Add the last paragraph
        if start_idx < len(text):
            paragraph_text = text[start_idx:]
            
            start_pos = None
            end_pos = None
            
            # Рассчитываем позиции только если родительский сегмент имеет действительные позиции
            if segment.start_position is not None:
                start_pos = segment.start_position + start_idx
                end_pos = segment.start_position + len(text)
                
            paragraph = TextSegment(
                document_id=segment.document_id,
                text=paragraph_text,
                start_position=start_pos,
                end_position=end_pos,
                language=segment.language,
                parent_id=segment.id,
                metadata={
                    "segment_type": "paragraph",
                    "parent_segment": str(segment.id)
                }
            )
            paragraphs.append(paragraph)
        
        return paragraphs
    
    def _segment_by_sentences(self, segment: TextSegment) -> List[TextSegment]:
        """Split a segment into sentences.
        
        Args:
            segment: Text segment to split
            
        Returns:
            List of sentence segments
        """
        text = segment.text
        sentences = []
        
        # Simple sentence splitting by common end punctuation
        # This is a simplified approach - for production, use spaCy or similar
        sentence_endings = []
        for match in re.finditer(r'[.!?]\s+', text):
            sentence_endings.append(match.end())
        
        # If no sentence breaks or only one sentence, handle overlapping chunks
        if not sentence_endings:
            return self._segment_by_length(segment)
        
        # Create sentence segments
        start_idx = 0
        for end_idx in sentence_endings:
            if end_idx - start_idx > self.max_segment_length:
                # Sentence is too long, break it up by length
                start_pos = None
                end_pos = None
                
                # Рассчитываем позиции только если родительский сегмент имеет действительные позиции
                if segment.start_position is not None:
                    start_pos = segment.start_position + start_idx
                    end_pos = segment.start_position + end_idx
                
                sub_segment = TextSegment(
                    document_id=segment.document_id,
                    text=text[start_idx:end_idx],
                    start_position=start_pos,
                    end_position=end_pos,
                    language=segment.language,
                    parent_id=segment.id,
                    metadata={
                        "segment_type": "long_sentence",
                        "parent_segment": str(segment.id)
                    }
                )
                sentences.extend(self._segment_by_length(sub_segment))
            else:
                # Create sentence segment
                start_pos = None
                end_pos = None
                
                # Рассчитываем позиции только если родительский сегмент имеет действительные позиции
                if segment.start_position is not None:
                    start_pos = segment.start_position + start_idx
                    end_pos = segment.start_position + end_idx
                
                sentence = TextSegment(
                    document_id=segment.document_id,
                    text=text[start_idx:end_idx],
                    start_position=start_pos,
                    end_position=end_pos,
                    language=segment.language,
                    parent_id=segment.id,
                    metadata={
                        "segment_type": "sentence",
                        "parent_segment": str(segment.id)
                    }
                )
                sentences.append(sentence)
            
            start_idx = end_idx
        
        # Add the last part if needed
        if start_idx < len(text):
            start_pos = None
            end_pos = None
            
            # Рассчитываем позиции только если родительский сегмент имеет действительные позиции
            if segment.start_position is not None:
                start_pos = segment.start_position + start_idx
                end_pos = segment.start_position + len(text)
            
            sentence = TextSegment(
                document_id=segment.document_id,
                text=text[start_idx:],
                start_position=start_pos,
                end_position=end_pos,
                language=segment.language,
                parent_id=segment.id,
                metadata={
                    "segment_type": "sentence",
                    "parent_segment": str(segment.id)
                }
            )
            sentences.append(sentence)
        
        return sentences
    
    def _segment_by_length(self, segment: TextSegment) -> List[TextSegment]:
        """Split a segment into chunks of maximum length with overlap.
        
        Args:
            segment: Text segment to split
            
        Returns:
            List of overlapping chunks
        """
        text = segment.text
        length = len(text)
        
        # If the segment is short enough, return it as is
        if length <= self.max_segment_length:
            return [segment]
        
        # Split into overlapping chunks
        chunks = []
        start_idx = 0
        
        while start_idx < length:
            # Calculate end position with boundary adjustment
            end_idx = min(start_idx + self.max_segment_length, length)
            
            # If not at the end and not at a word boundary, adjust
            if end_idx < length and text[end_idx] != ' ' and text[end_idx - 1] != ' ':
                # Try to find a space to break at
                space_idx = text.rfind(' ', start_idx, end_idx)
                if space_idx > start_idx:
                    end_idx = space_idx + 1  # Include the space
            
            # Create chunk segment
            start_pos = None
            end_pos = None
            
            # Рассчитываем позиции только если родительский сегмент имеет действительные позиции
            if segment.start_position is not None:
                start_pos = segment.start_position + start_idx
                end_pos = segment.start_position + end_idx
            
            chunk = TextSegment(
                document_id=segment.document_id,
                text=text[start_idx:end_idx],
                start_position=start_pos,
                end_position=end_pos,
                language=segment.language,
                parent_id=segment.id,
                metadata={
                    "segment_type": "chunk",
                    "parent_segment": str(segment.id)
                }
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_idx = end_idx - self.max_segment_overlap
            
            # Ensure we make progress
            if start_idx <= 0 or start_idx >= end_idx:
                start_idx = end_idx
        
        return chunks