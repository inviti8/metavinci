"""
HEAVYMETA Metadata Data Classes

This module contains all data classes for generating HEAVYMETA 3D asset metadata.
Ported from hvym CLI for use with the local API server.
"""

from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json
from typing import Optional, List, Dict, Any
import json


# =============================================================================
# Base Classes
# =============================================================================

@dataclass_json
@dataclass
class BaseDataClass:
    """Base data class with dictionary and JSON conversion properties."""

    @property
    def dictionary(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def json(self) -> str:
        return json.dumps(self.dictionary)


@dataclass_json
@dataclass
class WidgetDataClass(BaseDataClass):
    """
    Base data class for widget data.

    :param widget_type: Widget type to use
    :param show: If false, hide widget
    """
    widget_type: str
    show: bool


@dataclass_json
@dataclass
class SliderDataClass(WidgetDataClass):
    """
    Base data class for slider data.

    :param prop_slider_type: Slider type to use
    :param prop_action_type: Action type to use
    """
    prop_slider_type: str
    prop_action_type: str


# =============================================================================
# Collection & UI Classes
# =============================================================================

@dataclass_json
@dataclass
class CollectionDataClass(BaseDataClass):
    """
    Base data class for HVYM collection properties.

    :param collectionName: Name of collection
    :param collectionType: Type of collection ('multi', 'single')
    :param valProps: Value properties dictionary
    :param textValProps: Text properties dictionary
    :param callProps: Method call properties dictionary
    :param meshProps: Mesh properties dictionary
    :param meshSets: Mesh sets dictionary
    :param morphSets: Morph sets dictionary
    :param animProps: Animation properties dictionary
    :param matProps: Material properties dictionary
    :param materialSets: Material sets dictionary
    :param menuData: Menu data dictionary
    :param propLabelData: Property labels dictionary
    :param nodes: List of all nodes in the collection
    :param actionProps: Action properties dictionary
    """
    collectionName: str
    collectionType: str
    valProps: Dict[str, Any]
    textValProps: Dict[str, Any]
    callProps: Dict[str, Any]
    meshProps: Dict[str, Any]
    meshSets: Dict[str, Any]
    morphSets: Dict[str, Any]
    animProps: Dict[str, Any]
    matProps: Dict[str, Any]
    materialSets: Dict[str, Any]
    menuData: Dict[str, Any]
    propLabelData: Dict[str, Any]
    nodes: Dict[str, Any]
    actionProps: Dict[str, Any]


@dataclass_json
@dataclass
class MenuDataClass(BaseDataClass):
    """
    Base data class for HVYM menu properties.

    :param name: Menu name
    :param primary_color: Primary color of menu
    :param secondary_color: Secondary color of menu
    :param text_color: Text color of menu
    :param alignment: Alignment relative to transform ('CENTER', 'LEFT', 'RIGHT')
    """
    name: str
    primary_color: str
    secondary_color: str
    text_color: str
    alignment: str


@dataclass_json
@dataclass
class ActionDataClass(BaseDataClass):
    """
    Base data class for HVYM action properties.

    :param anim_type: Animation type to use
    :param set: Mesh ref list
    :param interaction: Interaction type to use
    :param sequence: How animation is sequenced
    :param additive: Set the type of animation blending
    """
    anim_type: str
    set: List[Any]
    interaction: str
    sequence: str
    additive: bool


@dataclass_json
@dataclass
class ActionMeshDataClass(ActionDataClass):
    """
    Action data class with model reference.

    :param model_ref: Model reference properties
    """
    model_ref: Dict[str, Any]


@dataclass_json
@dataclass
class PropertyLabelDataClass(BaseDataClass):
    """
    Base data class for property labels.

    :param value_prop_label: Value Property Label
    :param text_prop_label: Text Property Label
    :param call_prop_label: Call Property Label
    :param mesh_prop_label: Mesh Property Label
    :param mat_prop_label: Material Property Label
    :param anim_prop_label: Animation Property Label
    :param mesh_set_label: Mesh Set Label
    :param morph_set_label: Morph Set Label
    :param mat_set_label: Material Set Label
    """
    value_prop_label: str
    text_prop_label: str
    call_prop_label: str
    mesh_prop_label: str
    mat_prop_label: str
    anim_prop_label: str
    mesh_set_label: str
    morph_set_label: str
    mat_set_label: str


# =============================================================================
# Value Property Classes
# =============================================================================

@dataclass_json
@dataclass
class BehaviorDataClass(BaseDataClass):
    """
    Creates data object for a behavior definition.

    :param name: Method name
    :param trait_type: Trait Type
    :param values: Values
    :param use_method: If true, use defined method
    :param method: Method name
    :param behavior_type: Behavior Type
    :param use_behavior: Use Behavior if true
    """
    name: str
    trait_type: str
    values: str
    use_method: bool
    method: str
    behavior_type: str
    use_behavior: bool


@dataclass_json
@dataclass
class IntDataClass(SliderDataClass):
    """
    Creates data object for int data value property.

    :param default: Default integer value
    :param min: Minimum integer value
    :param max: Maximum integer value
    :param immutable: If immutable, property cannot be edited after minting
    """
    default: int
    min: int
    max: int
    immutable: bool


@dataclass_json
@dataclass
class IntDataBehaviorClass(IntDataClass):
    """
    Creates data object for int data value property with behaviors.

    :param behaviors: List of behaviors for this val prop
    """
    behaviors: List[Any]


@dataclass_json
@dataclass
class CrementalIntDataClass(IntDataClass):
    """
    Creates data object for incremental/decremental int value property.

    :param amount: The amount to increment or decrement
    """
    amount: int


@dataclass_json
@dataclass
class CrementalIntDataBehaviorClass(CrementalIntDataClass):
    """
    Creates data object for incremental/decremental int with behaviors.

    :param behaviors: List of behaviors for this val prop
    """
    behaviors: List[Any]


@dataclass_json
@dataclass
class FloatDataClass(SliderDataClass):
    """
    Creates data object for float data value property.

    :param default: Default float value
    :param min: Minimum float value
    :param max: Maximum float value
    :param immutable: If immutable, property cannot be edited after minting
    """
    default: float
    min: float
    max: float
    immutable: bool


@dataclass_json
@dataclass
class CrementalFloatDataClass(FloatDataClass):
    """
    Creates data object for incremental/decremental float value property.

    :param amount: The amount to increment or decrement
    """
    amount: float


@dataclass_json
@dataclass
class CrementalFloatDataBehaviorClass(CrementalFloatDataClass):
    """
    Creates data object for incremental/decremental float with behaviors.

    :param behaviors: List of behaviors for this val prop
    """
    behaviors: List[Any]


@dataclass_json
@dataclass
class SingleIntDataClass(BaseDataClass):
    """
    Creates data object for singular int data value property.

    :param name: Element name
    :param default: Default integer value
    :param min: Minimum integer value
    :param max: Maximum integer value
    """
    name: str
    default: int
    min: int
    max: int


@dataclass_json
@dataclass
class SingleFloatDataClass(BaseDataClass):
    """
    Creates data object for singular float data value property.

    :param name: Element name
    :param default: Default float value
    :param min: Minimum float value
    :param max: Maximum float value
    """
    name: str
    default: float
    min: float
    max: float


# =============================================================================
# Text & Call Classes
# =============================================================================

@dataclass_json
@dataclass
class TextDataClass(BaseDataClass):
    """
    Creates data object for a text item.

    :param name: Property name
    :param show: If false, hide widget
    :param immutable: If immutable, property cannot be edited after minting
    :param text: Text value
    :param widget_type: Widget type
    :param behaviors: List of behaviors for this val prop
    """
    name: str
    show: bool
    immutable: bool
    text: str
    widget_type: str
    behaviors: List[Any]


@dataclass_json
@dataclass
class CallDataClass(BaseDataClass):
    """
    Creates data object for a method call reference.

    :param name: Method name
    :param call_param: Call parameter
    """
    name: str
    call_param: str


# =============================================================================
# Mesh & Node Classes
# =============================================================================

@dataclass_json
@dataclass
class SingleMeshDataClass(BaseDataClass):
    """
    Creates data object for singular mesh reference.

    :param name: Mesh name
    :param visible: Mesh visibility
    """
    name: str
    visible: bool


@dataclass_json
@dataclass
class SingleNodeDataClass(BaseDataClass):
    """
    Creates data object for singular node reference.

    :param name: Node name
    :param type: Node type
    """
    name: str
    type: str


@dataclass_json
@dataclass
class MeshDataClass(WidgetDataClass):
    """
    Creates data object for a mesh reference.

    :param name: Mesh name
    :param visible: Mesh visibility
    """
    name: str
    visible: bool


@dataclass_json
@dataclass
class MeshSetDataClass(WidgetDataClass):
    """
    Creates data object for a mesh set.

    :param set: Mesh ref list
    :param selected_index: Selected index for the list
    """
    set: List[Any]
    selected_index: int


@dataclass_json
@dataclass
class MorphSetDataClass(WidgetDataClass):
    """
    Creates data object for a morph set.

    :param set: Morph ref list
    :param selected_index: Selected index for the list
    :param model_ref: Model reference properties
    """
    set: List[Any]
    selected_index: int
    model_ref: Dict[str, Any]


# =============================================================================
# Animation Classes
# =============================================================================

@dataclass_json
@dataclass
class AnimPropDataClass(WidgetDataClass):
    """
    Creates data object for animation property.

    :param name: Element name
    :param loop: Animation looping ('NONE', 'LoopRepeat', 'LoopOnce', 'ClampToggle', 'Clamp', 'PingPong')
    :param start: Start frame of animation
    :param end: End frame of animation
    :param blending: Animation blending type
    :param weight: Amount animation affects element
    :param play: If true, animation should play
    :param model_ref: Model reference properties
    """
    name: str
    loop: str
    start: int
    end: int
    blending: str
    weight: float
    play: bool
    model_ref: Dict[str, Any]


# =============================================================================
# Material Classes
# =============================================================================

@dataclass_json
@dataclass
class MatPropDataClass(WidgetDataClass):
    """
    Creates data object for material property reference.

    :param name: Element name
    :param type: Material type ('STANDARD', 'PBR', 'TOON')
    :param emissive: If true, material is emissive
    :param reflective: If true, material is reflective
    :param irridescent: If true, material is iridescent
    :param sheen: If true, material has sheen
    :param mat_ref: Object representation of the mesh material
    :param save_data: Material save data dictionary
    """
    name: str
    type: str
    emissive: bool
    reflective: bool
    irridescent: bool
    sheen: bool
    mat_ref: Dict[str, Any]
    save_data: Dict[str, Any]


@dataclass_json
@dataclass
class MatSetDataClass(WidgetDataClass):
    """
    Creates data object for material set.

    :param set: Material ref list
    :param mesh_set: Mesh ref list
    :param material_id: Material ID for assignment
    :param selected_index: Selected index for the list
    """
    set: List[Any]
    mesh_set: List[Any]
    material_id: int
    selected_index: int


@dataclass_json
@dataclass
class BasicMaterialClass(BaseDataClass):
    """
    Creates data object for basic material reference.

    :param color: Color hex string
    :param emissive: Emissive color hex string
    :param emissive_intensity: Emissive intensity
    """
    color: str
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


@dataclass_json
@dataclass
class LambertMaterialClass(BaseDataClass):
    """
    Creates data object for lambert material reference.

    :param color: Color hex string
    :param emissive: Emissive color hex string
    :param emissive_intensity: Emissive intensity
    """
    color: str
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


@dataclass_json
@dataclass
class PhongMaterialClass(BaseDataClass):
    """
    Creates data object for phong material reference.

    :param color: Color hex string
    :param specular: Specular color hex string
    :param shininess: Shininess value
    :param emissive: Emissive color hex string
    :param emissive_intensity: Emissive intensity
    """
    color: str
    specular: str
    shininess: float
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


@dataclass_json
@dataclass
class StandardMaterialClass(BaseDataClass):
    """
    Creates data object for standard material reference.

    :param color: Color hex string
    :param roughness: Roughness value
    :param metalness: Metalness value
    :param emissive: Emissive color hex string
    :param emissive_intensity: Emissive intensity
    """
    color: str
    roughness: float
    metalness: float
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


@dataclass_json
@dataclass
class PBRMaterialClass(BaseDataClass):
    """
    Creates data object for PBR material reference.

    :param color: Color hex string
    :param roughness: Roughness value
    :param metalness: Metalness value
    :param iridescent: If true, material has iridescent property
    :param sheen_color: Sheen color hex string
    :param sheen_weight: Sheen weight value
    :param emissive: Emissive color hex string
    :param emissive_intensity: Emissive intensity
    """
    color: str
    roughness: float
    metalness: float
    iridescent: Optional[bool] = None
    sheen_color: Optional[str] = None
    sheen_weight: Optional[float] = None
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


# =============================================================================
# Interactable Classes
# =============================================================================

@dataclass_json
@dataclass
class InteractableDataClass(BaseDataClass):
    """
    Base data class for HVYM interactable properties.

    :param interactable: Bool for interaction type
    :param has_return: If true, the associated call returns value
    :param interaction_type: Interaction type string
    :param selector_dir: Selector direction string
    :param name: Interaction name
    :param call: Interaction call
    :param default_text: Default text for interactable edit text
    :param text_scale: Amount to scale interactable text
    :param text_wrap: If true, text will wrap
    :param param_type: Parameter type string
    :param slider_param_type: Slider parameter type
    :param toggle_param_type: Toggle parameter type
    :param string_param: String parameter for call
    :param int_param: Int parameter for call
    :param float_default: Float default value
    :param float_min: Float minimum value
    :param float_max: Float maximum value
    :param int_default: Int default value
    :param int_min: Int minimum value
    :param int_max: Int maximum value
    :param toggle_state: Toggle state
    :param toggle_int: Toggle int value
    :param mesh_set: Mesh set list
    :param behavior: Behavior dictionary
    """
    interactable: bool
    has_return: bool
    interaction_type: str
    selector_dir: str
    name: str
    call: str
    default_text: str
    text_scale: float
    text_wrap: bool
    param_type: str
    slider_param_type: str
    toggle_param_type: str
    string_param: str
    int_param: int
    float_default: float
    float_min: float
    float_max: float
    int_default: int
    int_min: int
    int_max: int
    toggle_state: bool
    toggle_int: int
    mesh_set: List[Any]
    behavior: Dict[str, Any]


# =============================================================================
# Export all classes
# =============================================================================

__all__ = [
    # Base
    'BaseDataClass',
    'WidgetDataClass',
    'SliderDataClass',
    # Collection & UI
    'CollectionDataClass',
    'MenuDataClass',
    'ActionDataClass',
    'ActionMeshDataClass',
    'PropertyLabelDataClass',
    # Value Properties
    'BehaviorDataClass',
    'IntDataClass',
    'IntDataBehaviorClass',
    'CrementalIntDataClass',
    'CrementalIntDataBehaviorClass',
    'FloatDataClass',
    'CrementalFloatDataClass',
    'CrementalFloatDataBehaviorClass',
    'SingleIntDataClass',
    'SingleFloatDataClass',
    # Text & Call
    'TextDataClass',
    'CallDataClass',
    # Mesh & Node
    'SingleMeshDataClass',
    'SingleNodeDataClass',
    'MeshDataClass',
    'MeshSetDataClass',
    'MorphSetDataClass',
    # Animation
    'AnimPropDataClass',
    # Materials
    'MatPropDataClass',
    'MatSetDataClass',
    'BasicMaterialClass',
    'LambertMaterialClass',
    'PhongMaterialClass',
    'StandardMaterialClass',
    'PBRMaterialClass',
    # Interactable
    'InteractableDataClass',
]
