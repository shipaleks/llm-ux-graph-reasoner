"""Graph verification for the knowledge graph synthesis system."""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

from ..models import KnowledgeGraph, Entity, Relationship, TextSegment, SegmentCollection, SourceSpan
from ..config import settings

logger = logging.getLogger(__name__)


class GraphVerifier:
    """Verifies the consistency and accuracy of knowledge graphs.
    
    This class implements methods for verifying that a knowledge graph
    is consistent, that its elements are grounded in source text, and
    that it accurately represents the information in the source.
    """
    
    def __init__(self, 
               source_verification: bool = True,
               consistency_verification: bool = True):
        """Initialize the graph verifier.
        
        Args:
            source_verification: Whether to verify elements against source text
            consistency_verification: Whether to verify graph consistency
        """
        self.source_verification = source_verification
        self.consistency_verification = consistency_verification
    
    def verify(self, 
             graph: KnowledgeGraph,
             collection: Optional[SegmentCollection] = None) -> Tuple[bool, Dict[str, Any]]:
        """Verify a knowledge graph.
        
        Args:
            graph: Knowledge graph to verify
            collection: Optional segment collection for source verification
            
        Returns:
            (is_valid, results) tuple
        """
        results = {
            "verified": True,
            "entity_verification": {},
            "relationship_verification": {},
            "consistency_verification": {},
            "overall_confidence": 0.0,
            "issues": []
        }
        
        # Verify structural consistency
        if self.consistency_verification:
            consistency_results = self.verify_consistency(graph)
            results["consistency_verification"] = consistency_results
            
            if not consistency_results["verified"]:
                results["verified"] = False
                results["issues"].extend(consistency_results["issues"])
        
        # Verify against source text
        if self.source_verification and collection:
            # Verify entities
            entity_results = self.verify_entities(graph, collection)
            results["entity_verification"] = entity_results
            
            if not entity_results["verified"]:
                results["verified"] = False
                results["issues"].extend(entity_results["issues"])
            
            # Verify relationships
            rel_results = self.verify_relationships(graph, collection)
            results["relationship_verification"] = rel_results
            
            if not rel_results["verified"]:
                results["verified"] = False
                results["issues"].extend(rel_results["issues"])
        
        # Calculate overall confidence
        entity_confidences = [entity.confidence for entity in graph.entities.values()]
        relationship_confidences = [rel.confidence for rel in graph.relationships.values()]
        
        if entity_confidences and relationship_confidences:
            entity_avg = sum(entity_confidences) / len(entity_confidences)
            rel_avg = sum(relationship_confidences) / len(relationship_confidences)
            results["overall_confidence"] = (entity_avg + rel_avg) / 2
        elif entity_confidences:
            results["overall_confidence"] = sum(entity_confidences) / len(entity_confidences)
        elif relationship_confidences:
            results["overall_confidence"] = sum(relationship_confidences) / len(relationship_confidences)
        
        return results["verified"], results
    
    def verify_consistency(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Verify the structural consistency of a knowledge graph.
        
        Args:
            graph: Knowledge graph to verify
            
        Returns:
            Dictionary with verification results
        """
        issues = []
        
        # Check for empty graph
        if not graph.entities:
            issues.append("Graph has no entities")
        
        if not graph.relationships:
            issues.append("Graph has no relationships")
        
        # Check for dangling relationships
        for rel_id, rel in graph.relationships.items():
            if rel.source_id not in graph.entities:
                issues.append(f"Relationship {rel_id} has dangling source entity {rel.source_id}")
            
            if rel.target_id not in graph.entities:
                issues.append(f"Relationship {rel_id} has dangling target entity {rel.target_id}")
        
        # Check for duplicate entities
        entity_names = {}
        for entity_id, entity in graph.entities.items():
            key = (entity.name.lower(), entity.type.lower())
            
            if key in entity_names:
                issues.append(f"Duplicate entity: {entity.name} ({entity.type}) with IDs {entity_id} and {entity_names[key]}")
            else:
                entity_names[key] = entity_id
        
        # Check for self-relationships
        for rel_id, rel in graph.relationships.items():
            if rel.source_id == rel.target_id:
                source_entity = graph.get_entity(rel.source_id)
                if source_entity:
                    issues.append(f"Self-relationship: {source_entity.name} ({rel.type}) to itself")
        
        # Check for duplicate relationships
        rel_keys = {}
        for rel_id, rel in graph.relationships.items():
            key = (rel.source_id, rel.target_id, rel.type.lower())
            
            if key in rel_keys:
                source_entity = graph.get_entity(rel.source_id)
                target_entity = graph.get_entity(rel.target_id)
                
                if source_entity and target_entity:
                    issues.append(f"Duplicate relationship: {source_entity.name} ({rel.type}) to {target_entity.name} with IDs {rel_id} and {rel_keys[key]}")
            else:
                rel_keys[key] = rel_id
        
        # Calculate verification metrics
        total_entities = len(graph.entities)
        total_relationships = len(graph.relationships)
        dangling_relationships = sum(1 for issue in issues if "dangling" in issue)
        duplicate_entities = sum(1 for issue in issues if "Duplicate entity" in issue)
        duplicate_relationships = sum(1 for issue in issues if "Duplicate relationship" in issue)
        self_relationships = sum(1 for issue in issues if "Self-relationship" in issue)
        
        metrics = {
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "dangling_relationships": dangling_relationships,
            "duplicate_entities": duplicate_entities,
            "duplicate_relationships": duplicate_relationships,
            "self_relationships": self_relationships
        }
        
        # Determine if the graph is structurally consistent
        is_consistent = (
            total_entities > 0 and
            total_relationships > 0 and
            dangling_relationships == 0
        )
        
        return {
            "verified": is_consistent,
            "metrics": metrics,
            "issues": issues
        }
    
    def verify_entities(self, 
                      graph: KnowledgeGraph,
                      collection: SegmentCollection) -> Dict[str, Any]:
        """Verify entities against source text.
        
        Args:
            graph: Knowledge graph to verify
            collection: Segment collection for source verification
            
        Returns:
            Dictionary with verification results
        """
        issues = []
        verified_entities = []
        unverified_entities = []
        
        for entity_id, entity in graph.entities.items():
            # Check if the entity has a source span
            if not entity.source_span:
                unverified_entities.append(entity)
                issues.append(f"Entity {entity.name} ({entity.type}) has no source span")
                continue
            
            # Check if the segment exists
            if not entity.source_span.segment_id:
                unverified_entities.append(entity)
                issues.append(f"Entity {entity.name} ({entity.type}) has no segment ID")
                continue
            
            segment_id = UUID(entity.source_span.segment_id)
            segment = collection.get_segment(segment_id)
            
            if not segment:
                unverified_entities.append(entity)
                issues.append(f"Entity {entity.name} ({entity.type}) segment {segment_id} not found")
                continue
            
            # Check if the span is valid within the segment
            start = entity.source_span.start
            end = entity.source_span.end
            
            if start < 0 or end > len(segment.text) or start >= end:
                unverified_entities.append(entity)
                issues.append(f"Entity {entity.name} ({entity.type}) has invalid span: {start}-{end}")
                continue
            
            # Check if the entity name appears in the span
            span_text = segment.text[start:end]
            entity_name_lower = entity.name.lower()
            
            if entity_name_lower not in span_text.lower():
                unverified_entities.append(entity)
                issues.append(f"Entity {entity.name} ({entity.type}) not found in span text: {span_text}")
                continue
            
            # Entity is verified
            verified_entities.append(entity)
        
        # Calculate verification metrics
        total_entities = len(graph.entities)
        verified_count = len(verified_entities)
        unverified_count = len(unverified_entities)
        verification_rate = verified_count / total_entities if total_entities > 0 else 0
        
        metrics = {
            "total_entities": total_entities,
            "verified_entities": verified_count,
            "unverified_entities": unverified_count,
            "verification_rate": verification_rate
        }
        
        # Determine if entities are sufficiently verified
        is_verified = verification_rate >= 0.8  # 80% threshold
        
        return {
            "verified": is_verified,
            "metrics": metrics,
            "verified_entities": [entity.id for entity in verified_entities],
            "unverified_entities": [entity.id for entity in unverified_entities],
            "issues": issues
        }
    
    def verify_relationships(self, 
                         graph: KnowledgeGraph,
                         collection: SegmentCollection) -> Dict[str, Any]:
        """Verify relationships against source text.
        
        Args:
            graph: Knowledge graph to verify
            collection: Segment collection for source verification
            
        Returns:
            Dictionary with verification results
        """
        issues = []
        verified_relationships = []
        unverified_relationships = []
        
        for rel_id, rel in graph.relationships.items():
            # Get source and target entities
            source_entity = graph.get_entity(rel.source_id)
            target_entity = graph.get_entity(rel.target_id)
            
            if not source_entity or not target_entity:
                unverified_relationships.append(rel)
                issues.append(f"Relationship {rel.type} has missing entities")
                continue
            
            # Check if the relationship has a source span
            if not rel.source_span:
                unverified_relationships.append(rel)
                issues.append(f"Relationship {source_entity.name} ({rel.type}) {target_entity.name} has no source span")
                continue
            
            # Check if the segment exists
            if not rel.source_span.segment_id:
                unverified_relationships.append(rel)
                issues.append(f"Relationship {source_entity.name} ({rel.type}) {target_entity.name} has no segment ID")
                continue
            
            segment_id = UUID(rel.source_span.segment_id)
            segment = collection.get_segment(segment_id)
            
            if not segment:
                unverified_relationships.append(rel)
                issues.append(f"Relationship {source_entity.name} ({rel.type}) {target_entity.name} segment {segment_id} not found")
                continue
            
            # Check if the span is valid within the segment
            start = rel.source_span.start
            end = rel.source_span.end
            
            if start < 0 or end > len(segment.text) or start >= end:
                unverified_relationships.append(rel)
                issues.append(f"Relationship {source_entity.name} ({rel.type}) {target_entity.name} has invalid span: {start}-{end}")
                continue
            
            # Check if both entity names appear in the span
            span_text = segment.text[start:end].lower()
            source_name_lower = source_entity.name.lower()
            target_name_lower = target_entity.name.lower()
            
            if source_name_lower not in span_text or target_name_lower not in span_text:
                unverified_relationships.append(rel)
                issues.append(f"Relationship {source_entity.name} ({rel.type}) {target_entity.name} not fully present in span text")
                continue
            
            # Relationship is verified
            verified_relationships.append(rel)
        
        # Calculate verification metrics
        total_relationships = len(graph.relationships)
        verified_count = len(verified_relationships)
        unverified_count = len(unverified_relationships)
        verification_rate = verified_count / total_relationships if total_relationships > 0 else 0
        
        metrics = {
            "total_relationships": total_relationships,
            "verified_relationships": verified_count,
            "unverified_relationships": unverified_count,
            "verification_rate": verification_rate
        }
        
        # Determine if relationships are sufficiently verified
        is_verified = verification_rate >= 0.7  # 70% threshold
        
        return {
            "verified": is_verified,
            "metrics": metrics,
            "verified_relationships": [rel.id for rel in verified_relationships],
            "unverified_relationships": [rel.id for rel in unverified_relationships],
            "issues": issues
        }