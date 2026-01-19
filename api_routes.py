"""
HEAVYMETADATA API Routes

FastAPI router with endpoints for generating HEAVYMETA 3D asset metadata structures.
Includes both generation endpoints and parse endpoints for Blender GLTF extension data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from hvym_metadata import (
    # Base/Widget
    SliderDataClass,
    # Collection & UI
    CollectionDataClass,
    MenuDataClass,
    ActionDataClass,
    ActionMeshDataClass,
    PropertyLabelDataClass,
    # Value Properties
    BehaviorDataClass,
    IntDataClass,
    IntDataBehaviorClass,
    CrementalIntDataClass,
    CrementalIntDataBehaviorClass,
    FloatDataClass,
    CrementalFloatDataClass,
    CrementalFloatDataBehaviorClass,
    SingleIntDataClass,
    SingleFloatDataClass,
    # Text & Call
    TextDataClass,
    CallDataClass,
    # Mesh & Node
    SingleMeshDataClass,
    SingleNodeDataClass,
    MeshDataClass,
    MeshSetDataClass,
    MorphSetDataClass,
    # Animation
    AnimPropDataClass,
    # Materials
    MatPropDataClass,
    MatSetDataClass,
    BasicMaterialClass,
    LambertMaterialClass,
    PhongMaterialClass,
    StandardMaterialClass,
    PBRMaterialClass,
    # Interactable
    InteractableDataClass,
)

router = APIRouter(prefix="/api/v1", tags=["metadata"])


# =============================================================================
# Request Models
# =============================================================================

# --- Collection & UI ---

class CollectionRequest(BaseModel):
    collectionName: str
    collectionType: str = "multi"
    valProps: Optional[Dict[str, Any]] = None
    textValProps: Optional[Dict[str, Any]] = None
    callProps: Optional[Dict[str, Any]] = None
    meshProps: Optional[Dict[str, Any]] = None
    meshSets: Optional[Dict[str, Any]] = None
    morphSets: Optional[Dict[str, Any]] = None
    animProps: Optional[Dict[str, Any]] = None
    matProps: Optional[Dict[str, Any]] = None
    materialSets: Optional[Dict[str, Any]] = None
    menuData: Optional[Dict[str, Any]] = None
    propLabelData: Optional[Dict[str, Any]] = None
    nodes: Optional[Dict[str, Any]] = None
    actionProps: Optional[Dict[str, Any]] = None


class MenuRequest(BaseModel):
    name: str
    primary_color: str = "#FFFFFF"
    secondary_color: str = "#000000"
    text_color: str = "#FFFFFF"
    alignment: str = "CENTER"


class ActionRequest(BaseModel):
    anim_type: str
    set: List[Any] = []
    interaction: str
    sequence: str
    additive: bool = False
    model_ref: Optional[Dict[str, Any]] = None


class PropertyLabelsRequest(BaseModel):
    value_prop_label: str = "Properties"
    text_prop_label: str = "Text"
    call_prop_label: str = "Calls"
    mesh_prop_label: str = "Meshes"
    mat_prop_label: str = "Materials"
    anim_prop_label: str = "Animations"
    mesh_set_label: str = "Mesh Sets"
    morph_set_label: str = "Morph Sets"
    mat_set_label: str = "Material Sets"


# --- Value Properties ---

class IntPropertyRequest(BaseModel):
    widget_type: str = "INT"
    show: bool = True
    prop_slider_type: str = "RANGE"
    prop_action_type: str = "Setter"
    default: int = 0
    min: int = 0
    max: int = 100
    immutable: bool = False
    amount: Optional[int] = None
    behaviors: Optional[List[Any]] = None


class FloatPropertyRequest(BaseModel):
    widget_type: str = "FLOAT"
    show: bool = True
    prop_slider_type: str = "RANGE"
    prop_action_type: str = "Setter"
    default: float = 0.0
    min: float = 0.0
    max: float = 1.0
    immutable: bool = False
    amount: Optional[float] = None
    behaviors: Optional[List[Any]] = None


class SingleIntRequest(BaseModel):
    """Request for a named integer value (not a slider widget)."""
    name: str
    default: int = 0
    min: int = 0
    max: int = 100


class SingleFloatRequest(BaseModel):
    """Request for a named float value (not a slider widget)."""
    name: str
    default: float = 0.0
    min: float = 0.0
    max: float = 1.0


class SliderRequest(BaseModel):
    """Request for base slider widget data."""
    widget_type: str = "SLIDER"
    show: bool = True
    prop_slider_type: str = "RANGE"
    prop_action_type: str = "Setter"


class BehaviorRequest(BaseModel):
    name: str
    trait_type: str
    values: str
    use_method: bool = False
    method: str = ""
    behavior_type: str = ""
    use_behavior: bool = False


class TextPropertyRequest(BaseModel):
    name: str
    show: bool = True
    immutable: bool = False
    text: str = ""
    widget_type: str = "TEXT"
    behaviors: Optional[List[Any]] = None


class CallPropertyRequest(BaseModel):
    name: str
    call_param: str


# --- Mesh & Node ---

class MeshRequest(BaseModel):
    widget_type: str = "TOGGLE"
    show: bool = True
    name: str
    visible: bool = True


class MeshSetRequest(BaseModel):
    widget_type: str = "SELECT"
    show: bool = True
    set: List[Any] = []
    selected_index: int = 0


class MorphSetRequest(BaseModel):
    widget_type: str = "SELECT"
    show: bool = True
    set: List[Any] = []
    selected_index: int = 0
    model_ref: Dict[str, Any] = {}


class NodeRequest(BaseModel):
    name: str
    type: str


class SingleMeshRequest(BaseModel):
    """Request for a single mesh reference (without widget data)."""
    name: str
    visible: bool = True


# --- Animation ---

class AnimationRequest(BaseModel):
    widget_type: str = "TOGGLE"
    show: bool = True
    name: str
    loop: str = "NONE"
    start: int = 0
    end: int = 100
    blending: str = "NORMAL"
    weight: float = 1.0
    play: bool = False
    model_ref: Dict[str, Any] = {}


# --- Materials ---

class BasicMaterialRequest(BaseModel):
    color: str = "#FFFFFF"
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


class LambertMaterialRequest(BaseModel):
    color: str = "#FFFFFF"
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


class PhongMaterialRequest(BaseModel):
    color: str = "#FFFFFF"
    specular: str = "#111111"
    shininess: float = 30.0
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


class StandardMaterialRequest(BaseModel):
    color: str = "#FFFFFF"
    roughness: float = 0.5
    metalness: float = 0.0
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


class PBRMaterialRequest(BaseModel):
    color: str = "#FFFFFF"
    roughness: float = 0.5
    metalness: float = 0.0
    iridescent: Optional[bool] = None
    sheen_color: Optional[str] = None
    sheen_weight: Optional[float] = None
    emissive: Optional[str] = None
    emissive_intensity: Optional[float] = None


class MatPropRequest(BaseModel):
    widget_type: str = "MULTI"
    show: bool = True
    name: str
    type: str = "STANDARD"
    emissive: bool = False
    reflective: bool = False
    irridescent: bool = False
    sheen: bool = False
    mat_ref: Dict[str, Any] = {}
    save_data: Dict[str, Any] = {}


class MatSetRequest(BaseModel):
    widget_type: str = "SELECT"
    show: bool = True
    set: List[Any] = []
    mesh_set: List[Any] = []
    material_id: int = 0
    selected_index: int = 0


# --- Interactable ---

class InteractableRequest(BaseModel):
    interactable: bool = True
    has_return: bool = False
    interaction_type: str = ""
    selector_dir: str = ""
    name: str = ""
    call: str = ""
    default_text: str = ""
    text_scale: float = 1.0
    text_wrap: bool = False
    param_type: str = ""
    slider_param_type: str = ""
    toggle_param_type: str = ""
    string_param: str = ""
    int_param: int = 0
    float_default: float = 0.0
    float_min: float = 0.0
    float_max: float = 1.0
    int_default: int = 0
    int_min: int = 0
    int_max: int = 100
    toggle_state: bool = False
    toggle_int: int = 0
    mesh_set: List[Any] = []
    behavior: Dict[str, Any] = {}


# --- Parse Request Models ---

class ValPropParseRequest(BaseModel):
    """Request model for parsing raw Blender value properties."""
    prop_action_type: str = Field(..., description="Immutable, Static, Incremental, Decremental, Bicremental, Setter")
    prop_value_type: str = Field("Int", description="Int or Float")
    prop_slider_type: str = "RANGE"
    show: bool = True
    prop_immutable: bool = False
    int_default: int = 0
    int_min: int = 0
    int_max: int = 100
    int_amount: int = 1
    float_default: float = 0.0
    float_min: float = 0.0
    float_max: float = 1.0
    float_amount: float = 0.1
    behavior_set: Optional[List[Any]] = None


class BlenderCollectionParseRequest(BaseModel):
    """Request model for parsing full Blender collection export."""
    collection_name: str
    collection_type: str
    collection_id: str
    collection_json: Dict[str, Any]
    menu_json: Dict[str, Any]
    nodes_json: Dict[str, Any]
    actions_json: Dict[str, Any]


class InteractablesParseRequest(BaseModel):
    """Request model for parsing Blender interactables."""
    obj_data: Dict[str, Any]


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "running", "service": "heavymetadata"}


@router.get("/status")
async def get_status():
    """API status and available endpoints."""
    return {
        "api_version": "1.0.0",
        "service": "HEAVYMETADATA",
        "endpoints": {
            "health": "/api/v1/health",
            "status": "/api/v1/status",
            "collection": "/api/v1/collection",
            "properties": {
                "int": "/api/v1/property/int",
                "float": "/api/v1/property/float",
                "text": "/api/v1/property/text",
                "behavior": "/api/v1/behavior",
                "call": "/api/v1/call",
            },
            "materials": {
                "basic": "/api/v1/material/basic",
                "lambert": "/api/v1/material/lambert",
                "phong": "/api/v1/material/phong",
                "standard": "/api/v1/material/standard",
                "pbr": "/api/v1/material/pbr",
                "mat-prop": "/api/v1/mat-prop",
                "mat-set": "/api/v1/mat-set",
            },
            "mesh": {
                "mesh": "/api/v1/mesh",
                "mesh-set": "/api/v1/mesh-set",
                "morph-set": "/api/v1/morph-set",
                "node": "/api/v1/node",
                "single-mesh": "/api/v1/single/mesh",
            },
            "animation": "/api/v1/animation",
            "ui": {
                "menu": "/api/v1/menu",
                "action": "/api/v1/action",
                "labels": "/api/v1/labels",
                "slider": "/api/v1/slider",
                "single-int": "/api/v1/single/int",
                "single-float": "/api/v1/single/float",
            },
            "interactable": "/api/v1/interactable",
            "parse": {
                "val-prop": "/api/v1/parse/val-prop",
                "behavior-val-prop": "/api/v1/parse/behavior-val-prop",
                "blender-collection": "/api/v1/parse/blender-collection",
                "interactables": "/api/v1/parse/interactables",
            }
        }
    }


# =============================================================================
# Collection Endpoint
# =============================================================================

@router.post("/collection")
async def create_collection(req: CollectionRequest):
    """Generate a complete HVYM collection metadata structure."""
    data = CollectionDataClass(
        collectionName=req.collectionName,
        collectionType=req.collectionType,
        valProps=req.valProps or {},
        textValProps=req.textValProps or {},
        callProps=req.callProps or {},
        meshProps=req.meshProps or {},
        meshSets=req.meshSets or {},
        morphSets=req.morphSets or {},
        animProps=req.animProps or {},
        matProps=req.matProps or {},
        materialSets=req.materialSets or {},
        menuData=req.menuData or {},
        propLabelData=req.propLabelData or {},
        nodes=req.nodes or {},
        actionProps=req.actionProps or {},
    )
    return data.dictionary


# =============================================================================
# Value Property Endpoints
# =============================================================================

@router.post("/property/int")
async def create_int_property(req: IntPropertyRequest):
    """Generate an integer value property metadata structure."""
    # Check if cremental (has amount) or behavior version needed
    if req.behaviors is not None:
        if req.amount is not None:
            data = CrementalIntDataBehaviorClass(
                widget_type=req.widget_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.default,
                min=req.min,
                max=req.max,
                immutable=req.immutable,
                amount=req.amount,
                behaviors=req.behaviors,
            )
        else:
            data = IntDataBehaviorClass(
                widget_type=req.widget_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.default,
                min=req.min,
                max=req.max,
                immutable=req.immutable,
                behaviors=req.behaviors,
            )
    elif req.amount is not None:
        data = CrementalIntDataClass(
            widget_type=req.widget_type,
            show=req.show,
            prop_slider_type=req.prop_slider_type,
            prop_action_type=req.prop_action_type,
            default=req.default,
            min=req.min,
            max=req.max,
            immutable=req.immutable,
            amount=req.amount,
        )
    else:
        data = IntDataClass(
            widget_type=req.widget_type,
            show=req.show,
            prop_slider_type=req.prop_slider_type,
            prop_action_type=req.prop_action_type,
            default=req.default,
            min=req.min,
            max=req.max,
            immutable=req.immutable,
        )
    return data.dictionary


@router.post("/property/float")
async def create_float_property(req: FloatPropertyRequest):
    """Generate a float value property metadata structure."""
    if req.behaviors is not None:
        if req.amount is not None:
            data = CrementalFloatDataBehaviorClass(
                widget_type=req.widget_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.default,
                min=req.min,
                max=req.max,
                immutable=req.immutable,
                amount=req.amount,
                behaviors=req.behaviors,
            )
        else:
            # Float doesn't have a non-cremental behavior class, use cremental with amount=0
            data = CrementalFloatDataBehaviorClass(
                widget_type=req.widget_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.default,
                min=req.min,
                max=req.max,
                immutable=req.immutable,
                amount=0.0,
                behaviors=req.behaviors,
            )
    elif req.amount is not None:
        data = CrementalFloatDataClass(
            widget_type=req.widget_type,
            show=req.show,
            prop_slider_type=req.prop_slider_type,
            prop_action_type=req.prop_action_type,
            default=req.default,
            min=req.min,
            max=req.max,
            immutable=req.immutable,
            amount=req.amount,
        )
    else:
        data = FloatDataClass(
            widget_type=req.widget_type,
            show=req.show,
            prop_slider_type=req.prop_slider_type,
            prop_action_type=req.prop_action_type,
            default=req.default,
            min=req.min,
            max=req.max,
            immutable=req.immutable,
        )
    return data.dictionary


@router.post("/property/text")
async def create_text_property(req: TextPropertyRequest):
    """Generate a text property metadata structure."""
    data = TextDataClass(
        name=req.name,
        show=req.show,
        immutable=req.immutable,
        text=req.text,
        widget_type=req.widget_type,
        behaviors=req.behaviors or [],
    )
    return data.dictionary


@router.post("/behavior")
async def create_behavior(req: BehaviorRequest):
    """Generate a behavior definition metadata structure."""
    data = BehaviorDataClass(
        name=req.name,
        trait_type=req.trait_type,
        values=req.values,
        use_method=req.use_method,
        method=req.method,
        behavior_type=req.behavior_type,
        use_behavior=req.use_behavior,
    )
    return data.dictionary


@router.post("/call")
async def create_call_property(req: CallPropertyRequest):
    """Generate a call property metadata structure."""
    data = CallDataClass(
        name=req.name,
        call_param=req.call_param,
    )
    return data.dictionary


# =============================================================================
# Single Value & Slider Endpoints (UI Elements)
# =============================================================================

@router.post("/single/int")
async def create_single_int(req: SingleIntRequest):
    """Generate a named integer value metadata structure (not a slider widget)."""
    data = SingleIntDataClass(
        name=req.name,
        default=req.default,
        min=req.min,
        max=req.max,
    )
    return data.dictionary


@router.post("/single/float")
async def create_single_float(req: SingleFloatRequest):
    """Generate a named float value metadata structure (not a slider widget)."""
    data = SingleFloatDataClass(
        name=req.name,
        default=req.default,
        min=req.min,
        max=req.max,
    )
    return data.dictionary


@router.post("/slider")
async def create_slider(req: SliderRequest):
    """Generate a base slider widget metadata structure."""
    data = SliderDataClass(
        widget_type=req.widget_type,
        show=req.show,
        prop_slider_type=req.prop_slider_type,
        prop_action_type=req.prop_action_type,
    )
    return data.dictionary


# =============================================================================
# Mesh & Node Endpoints
# =============================================================================

@router.post("/mesh")
async def create_mesh_property(req: MeshRequest):
    """Generate a mesh property metadata structure."""
    data = MeshDataClass(
        widget_type=req.widget_type,
        show=req.show,
        name=req.name,
        visible=req.visible,
    )
    return data.dictionary


@router.post("/mesh-set")
async def create_mesh_set(req: MeshSetRequest):
    """Generate a mesh set metadata structure."""
    data = MeshSetDataClass(
        widget_type=req.widget_type,
        show=req.show,
        set=req.set,
        selected_index=req.selected_index,
    )
    return data.dictionary


@router.post("/morph-set")
async def create_morph_set(req: MorphSetRequest):
    """Generate a morph set metadata structure."""
    data = MorphSetDataClass(
        widget_type=req.widget_type,
        show=req.show,
        set=req.set,
        selected_index=req.selected_index,
        model_ref=req.model_ref,
    )
    return data.dictionary


@router.post("/node")
async def create_node(req: NodeRequest):
    """Generate a node reference metadata structure."""
    data = SingleNodeDataClass(
        name=req.name,
        type=req.type,
    )
    return data.dictionary


@router.post("/single/mesh")
async def create_single_mesh(req: SingleMeshRequest):
    """Generate a single mesh reference metadata structure (without widget data)."""
    data = SingleMeshDataClass(
        name=req.name,
        visible=req.visible,
    )
    return data.dictionary


# =============================================================================
# Animation Endpoint
# =============================================================================

@router.post("/animation")
async def create_animation_property(req: AnimationRequest):
    """Generate an animation property metadata structure."""
    data = AnimPropDataClass(
        widget_type=req.widget_type,
        show=req.show,
        name=req.name,
        loop=req.loop,
        start=req.start,
        end=req.end,
        blending=req.blending,
        weight=req.weight,
        play=req.play,
        model_ref=req.model_ref,
    )
    return data.dictionary


# =============================================================================
# Material Endpoints
# =============================================================================

@router.post("/material/basic")
async def create_basic_material(req: BasicMaterialRequest):
    """Generate a basic material metadata structure."""
    data = BasicMaterialClass(
        color=req.color,
        emissive=req.emissive,
        emissive_intensity=req.emissive_intensity,
    )
    return data.dictionary


@router.post("/material/lambert")
async def create_lambert_material(req: LambertMaterialRequest):
    """Generate a lambert material metadata structure."""
    data = LambertMaterialClass(
        color=req.color,
        emissive=req.emissive,
        emissive_intensity=req.emissive_intensity,
    )
    return data.dictionary


@router.post("/material/phong")
async def create_phong_material(req: PhongMaterialRequest):
    """Generate a phong material metadata structure."""
    data = PhongMaterialClass(
        color=req.color,
        specular=req.specular,
        shininess=req.shininess,
        emissive=req.emissive,
        emissive_intensity=req.emissive_intensity,
    )
    return data.dictionary


@router.post("/material/standard")
async def create_standard_material(req: StandardMaterialRequest):
    """Generate a standard material metadata structure."""
    data = StandardMaterialClass(
        color=req.color,
        roughness=req.roughness,
        metalness=req.metalness,
        emissive=req.emissive,
        emissive_intensity=req.emissive_intensity,
    )
    return data.dictionary


@router.post("/material/pbr")
async def create_pbr_material(req: PBRMaterialRequest):
    """Generate a PBR material metadata structure."""
    data = PBRMaterialClass(
        color=req.color,
        roughness=req.roughness,
        metalness=req.metalness,
        iridescent=req.iridescent,
        sheen_color=req.sheen_color,
        sheen_weight=req.sheen_weight,
        emissive=req.emissive,
        emissive_intensity=req.emissive_intensity,
    )
    return data.dictionary


@router.post("/mat-prop")
async def create_mat_prop(req: MatPropRequest):
    """Generate a material property reference metadata structure."""
    data = MatPropDataClass(
        widget_type=req.widget_type,
        show=req.show,
        name=req.name,
        type=req.type,
        emissive=req.emissive,
        reflective=req.reflective,
        irridescent=req.irridescent,
        sheen=req.sheen,
        mat_ref=req.mat_ref,
        save_data=req.save_data,
    )
    return data.dictionary


@router.post("/mat-set")
async def create_mat_set(req: MatSetRequest):
    """Generate a material set metadata structure."""
    data = MatSetDataClass(
        widget_type=req.widget_type,
        show=req.show,
        set=req.set,
        mesh_set=req.mesh_set,
        material_id=req.material_id,
        selected_index=req.selected_index,
    )
    return data.dictionary


# =============================================================================
# UI Endpoints
# =============================================================================

@router.post("/menu")
async def create_menu(req: MenuRequest):
    """Generate a menu configuration metadata structure."""
    data = MenuDataClass(
        name=req.name,
        primary_color=req.primary_color,
        secondary_color=req.secondary_color,
        text_color=req.text_color,
        alignment=req.alignment,
    )
    return data.dictionary


@router.post("/action")
async def create_action(req: ActionRequest):
    """Generate an action configuration metadata structure."""
    if req.model_ref is not None:
        data = ActionMeshDataClass(
            anim_type=req.anim_type,
            set=req.set,
            interaction=req.interaction,
            sequence=req.sequence,
            additive=req.additive,
            model_ref=req.model_ref,
        )
    else:
        data = ActionDataClass(
            anim_type=req.anim_type,
            set=req.set,
            interaction=req.interaction,
            sequence=req.sequence,
            additive=req.additive,
        )
    return data.dictionary


@router.post("/labels")
async def create_property_labels(req: PropertyLabelsRequest):
    """Generate property labels configuration metadata structure."""
    data = PropertyLabelDataClass(
        value_prop_label=req.value_prop_label,
        text_prop_label=req.text_prop_label,
        call_prop_label=req.call_prop_label,
        mesh_prop_label=req.mesh_prop_label,
        mat_prop_label=req.mat_prop_label,
        anim_prop_label=req.anim_prop_label,
        mesh_set_label=req.mesh_set_label,
        morph_set_label=req.morph_set_label,
        mat_set_label=req.mat_set_label,
    )
    return data.dictionary


# =============================================================================
# Interactable Endpoint
# =============================================================================

@router.post("/interactable")
async def create_interactable(req: InteractableRequest):
    """Generate an interactable configuration metadata structure."""
    data = InteractableDataClass(
        interactable=req.interactable,
        has_return=req.has_return,
        interaction_type=req.interaction_type,
        selector_dir=req.selector_dir,
        name=req.name,
        call=req.call,
        default_text=req.default_text,
        text_scale=req.text_scale,
        text_wrap=req.text_wrap,
        param_type=req.param_type,
        slider_param_type=req.slider_param_type,
        toggle_param_type=req.toggle_param_type,
        string_param=req.string_param,
        int_param=req.int_param,
        float_default=req.float_default,
        float_min=req.float_min,
        float_max=req.float_max,
        int_default=req.int_default,
        int_min=req.int_min,
        int_max=req.int_max,
        toggle_state=req.toggle_state,
        toggle_int=req.toggle_int,
        mesh_set=req.mesh_set,
        behavior=req.behavior,
    )
    return data.dictionary


# =============================================================================
# Parse Endpoints (from GLTF extension / Blender export)
# =============================================================================

def _create_text_behavior(name: str, use_method: bool, method: str, behavior_type: str, use_behavior: bool) -> Dict[str, Any]:
    """Helper to create behavior dictionary for text/interactable parsing."""
    return BehaviorDataClass(
        name=name,
        trait_type="text",
        values="",
        use_method=use_method,
        method=method,
        behavior_type=behavior_type,
        use_behavior=use_behavior,
    ).dictionary


@router.post("/parse/val-prop")
async def parse_val_prop(req: ValPropParseRequest):
    """
    Parse raw Blender value property into HVYM int/float data class.

    Equivalent to hvym CLI parse_val_prop() function.
    """
    result = None

    if req.prop_action_type in ['Immutable', 'Static']:
        if req.prop_value_type == 'Float':
            result = FloatDataClass(
                widget_type=req.prop_slider_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.float_default,
                min=req.float_min,
                max=req.float_max,
                immutable=req.prop_immutable,
            ).dictionary
        else:
            result = IntDataClass(
                widget_type=req.prop_slider_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.int_default,
                min=req.int_min,
                max=req.int_max,
                immutable=req.prop_immutable,
            ).dictionary
    else:
        if req.prop_value_type == 'Float':
            result = CrementalFloatDataClass(
                widget_type=req.prop_slider_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.float_default,
                min=req.float_min,
                max=req.float_max,
                immutable=req.prop_immutable,
                amount=req.float_amount,
            ).dictionary
        else:
            result = CrementalIntDataClass(
                widget_type=req.prop_slider_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.int_default,
                min=req.int_min,
                max=req.int_max,
                immutable=req.prop_immutable,
                amount=req.int_amount,
            ).dictionary

    return result


@router.post("/parse/behavior-val-prop")
async def parse_behavior_val_prop(req: ValPropParseRequest):
    """
    Parse property with behaviors into HVYM behavior data class.

    Equivalent to hvym CLI parse_behavior_val_prop() function.
    """
    behaviors = req.behavior_set or []
    result = None

    if req.prop_action_type in ['Immutable', 'Static']:
        if req.prop_value_type == 'Float':
            # Note: Using Int behavior class as in original hvym CLI
            result = IntDataBehaviorClass(
                widget_type=req.prop_slider_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=int(req.float_default),
                min=int(req.float_min),
                max=int(req.float_max),
                immutable=req.prop_immutable,
                behaviors=behaviors,
            ).dictionary
        else:
            result = IntDataBehaviorClass(
                widget_type=req.prop_slider_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.int_default,
                min=req.int_min,
                max=req.int_max,
                immutable=req.prop_immutable,
                behaviors=behaviors,
            ).dictionary
    else:
        if req.prop_value_type == 'Float':
            result = CrementalFloatDataBehaviorClass(
                widget_type=req.prop_slider_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.float_default,
                min=req.float_min,
                max=req.float_max,
                immutable=req.prop_immutable,
                amount=req.float_amount,
                behaviors=behaviors,
            ).dictionary
        else:
            result = CrementalIntDataBehaviorClass(
                widget_type=req.prop_slider_type,
                show=req.show,
                prop_slider_type=req.prop_slider_type,
                prop_action_type=req.prop_action_type,
                default=req.int_default,
                min=req.int_min,
                max=req.int_max,
                immutable=req.prop_immutable,
                amount=req.int_amount,
                behaviors=behaviors,
            ).dictionary

    return result


@router.post("/parse/blender-collection")
async def parse_blender_collection(req: BlenderCollectionParseRequest):
    """
    Parse full Blender collection export into HVYM format.

    Equivalent to hvym CLI parse_blender_hvym_collection() function.
    Takes collection, menu, nodes, and actions JSON data and returns
    a complete CollectionData structure.
    """
    col_data = req.collection_json
    menu_data = req.menu_json
    node_data = req.nodes_json
    action_data = req.actions_json

    val_props = {}
    text_props = {}
    call_props = {}
    mesh_props = {}
    mesh_sets = {}
    morph_sets = {}
    anim_props = {}
    mat_props = {}
    mat_sets = {}
    col_menu = {}
    prop_label_data = {}
    action_props = {}

    # Process collection data
    for i in col_data:
        if i.isdigit():
            obj = col_data[i]

            # Parse value properties
            int_props = None
            if obj.get('behavior_set') is not None:
                # Use behavior variant
                behavior_req = ValPropParseRequest(
                    prop_action_type=obj.get('prop_action_type', 'Setter'),
                    prop_value_type=obj.get('prop_value_type', 'Int'),
                    prop_slider_type=obj.get('prop_slider_type', 'RANGE'),
                    show=obj.get('show', True),
                    prop_immutable=obj.get('prop_immutable', False),
                    int_default=obj.get('int_default', 0),
                    int_min=obj.get('int_min', 0),
                    int_max=obj.get('int_max', 100),
                    int_amount=obj.get('int_amount', 1),
                    float_default=obj.get('float_default', 0.0),
                    float_min=obj.get('float_min', 0.0),
                    float_max=obj.get('float_max', 1.0),
                    float_amount=obj.get('float_amount', 0.1),
                    behavior_set=obj.get('behavior_set'),
                )
                int_props = await parse_behavior_val_prop(behavior_req)
            else:
                val_req = ValPropParseRequest(
                    prop_action_type=obj.get('prop_action_type', 'Setter'),
                    prop_value_type=obj.get('prop_value_type', 'Int'),
                    prop_slider_type=obj.get('prop_slider_type', 'RANGE'),
                    show=obj.get('show', True),
                    prop_immutable=obj.get('prop_immutable', False),
                    int_default=obj.get('int_default', 0),
                    int_min=obj.get('int_min', 0),
                    int_max=obj.get('int_max', 100),
                    int_amount=obj.get('int_amount', 1),
                    float_default=obj.get('float_default', 0.0),
                    float_min=obj.get('float_min', 0.0),
                    float_max=obj.get('float_max', 1.0),
                    float_amount=obj.get('float_amount', 0.1),
                )
                int_props = await parse_val_prop(val_req)

            trait_type = obj.get('trait_type', '')

            if trait_type == 'property':
                val_props[obj['type']] = int_props

            elif trait_type == 'text':
                text_props[obj['type']] = TextDataClass(
                    name=obj['type'],
                    show=obj.get('show', True),
                    immutable=obj.get('prop_immutable', False),
                    text=obj.get('text_value', ''),
                    widget_type=obj.get('prop_text_widget_type', 'TEXT'),
                    behaviors=obj.get('behavior_set') or [],
                ).dictionary

            elif trait_type == 'call':
                call_props[obj['type']] = CallDataClass(
                    name=obj['type'],
                    call_param=obj.get('call_param', ''),
                ).dictionary

            elif trait_type == 'mesh':
                if obj.get('model_ref') is not None:
                    mesh_props[obj['type']] = MeshDataClass(
                        widget_type=obj.get('prop_toggle_type', 'TOGGLE'),
                        show=obj.get('show', True),
                        name=obj['model_ref']['name'],
                        visible=obj.get('visible', True),
                    ).dictionary

            elif trait_type == 'mesh_set':
                mesh_sets[obj['type']] = MeshSetDataClass(
                    widget_type=obj.get('prop_selector_type', 'SELECT'),
                    show=obj.get('show', True),
                    set=obj.get('mesh_set', []),
                    selected_index=0,
                ).dictionary

            elif trait_type == 'morph_set':
                morph_sets[obj['type']] = MorphSetDataClass(
                    widget_type=obj.get('prop_selector_type', 'SELECT'),
                    show=obj.get('show', True),
                    set=obj.get('morph_set', []),
                    selected_index=0,
                    model_ref=obj.get('model_ref', {}),
                ).dictionary

            elif trait_type == 'anim':
                widget_type = obj.get('prop_toggle_type', 'TOGGLE')
                if obj.get('anim_loop') == 'Clamp':
                    widget_type = obj.get('prop_anim_slider_type', 'SLIDER')
                anim_props[obj['type']] = AnimPropDataClass(
                    widget_type=widget_type,
                    show=obj.get('show', True),
                    name=obj['type'],
                    loop=obj.get('anim_loop', 'NONE'),
                    start=obj.get('anim_start', 0),
                    end=obj.get('anim_end', 100),
                    blending=obj.get('anim_blending', 'NORMAL'),
                    weight=obj.get('anim_weight', 1.0),
                    play=obj.get('anim_play', False),
                    model_ref=obj.get('model_ref', {}),
                ).dictionary

            elif trait_type == 'mat_prop' and 'mat_ref' in obj:
                mat_props[obj['type']] = MatPropDataClass(
                    widget_type=obj.get('prop_multi_widget_type', 'MULTI'),
                    show=obj.get('show', True),
                    name=obj['mat_ref']['name'],
                    type=obj.get('mat_type', 'STANDARD'),
                    emissive=obj.get('mat_emissive', False),
                    reflective=obj.get('mat_reflective', False),
                    irridescent=obj.get('mat_iridescent', False),
                    sheen=obj.get('mat_sheen', False),
                    mat_ref=obj.get('mat_ref', {}),
                    save_data={},  # Would need _mat_save_data helper
                ).dictionary

            elif trait_type == 'mat_set':
                mat_sets[obj['type']] = MatSetDataClass(
                    widget_type=obj.get('prop_selector_type', 'SELECT'),
                    show=obj.get('show', True),
                    set=obj.get('mat_set', []),
                    mesh_set=obj.get('mesh_set_name', []),
                    material_id=obj.get('material_id', 0),
                    selected_index=0,
                ).dictionary

            # Property labels
            prop_label_data = PropertyLabelDataClass(
                value_prop_label=obj.get('value_prop_label', 'Properties'),
                text_prop_label=obj.get('text_prop_label', 'Text'),
                call_prop_label=obj.get('call_prop_label', 'Calls'),
                mesh_prop_label=obj.get('mesh_prop_label', 'Meshes'),
                mat_prop_label=obj.get('mat_prop_label', 'Materials'),
                anim_prop_label=obj.get('anim_prop_label', 'Animations'),
                mesh_set_label=obj.get('mesh_set_label', 'Mesh Sets'),
                morph_set_label=obj.get('morph_set_label', 'Morph Sets'),
                mat_set_label=obj.get('mat_set_label', 'Material Sets'),
            ).dictionary

    # Process menu data
    for i in menu_data:
        if i.isdigit():
            obj = menu_data[i]
            col_menu = MenuDataClass(
                name=obj.get('menu_name', ''),
                primary_color=obj.get('menu_primary_color', '#FFFFFF'),
                secondary_color=obj.get('menu_secondary_color', '#000000'),
                text_color=obj.get('menu_text_color', '#FFFFFF'),
                alignment=obj.get('menu_alignment', 'CENTER'),
            ).dictionary
            if obj.get('collection_id') == req.collection_id:
                break

    # Process action data
    for i in action_data:
        if i.isdigit():
            obj = action_data[i]
            if obj.get('trait_type') == 'mesh_action':
                action_props[obj['type']] = ActionMeshDataClass(
                    anim_type=obj.get('trait_type', ''),
                    set=obj.get('action_set', []),
                    interaction=obj.get('mesh_interaction_type', ''),
                    sequence=obj.get('sequence_type', ''),
                    additive=obj.get('additive', False),
                    model_ref=obj.get('model_ref', {}),
                ).dictionary
            else:
                action_props[obj['type']] = ActionDataClass(
                    anim_type=obj.get('trait_type', ''),
                    set=obj.get('action_set', []),
                    interaction=obj.get('anim_interaction_type', ''),
                    sequence=obj.get('sequence_type', ''),
                    additive=obj.get('additive', False),
                ).dictionary

    # Build final collection
    data = CollectionDataClass(
        collectionName=req.collection_name,
        collectionType=req.collection_type,
        valProps=val_props,
        textValProps=text_props,
        callProps=call_props,
        meshProps=mesh_props,
        meshSets=mesh_sets,
        morphSets=morph_sets,
        animProps=anim_props,
        matProps=mat_props,
        materialSets=mat_sets,
        menuData=col_menu,
        propLabelData=prop_label_data,
        nodes=node_data,
        actionProps=action_props,
    )

    return data.dictionary


@router.post("/parse/interactables")
async def parse_interactables(req: InteractablesParseRequest):
    """
    Parse Blender interactables into HVYM interactable data structures.

    Equivalent to hvym CLI parse_blender_hvym_interactables() function.
    """
    objs = req.obj_data
    data = {}

    for key in objs:
        obj = objs[key]
        if obj.get('hvym_interactable'):
            # Build mesh set from children
            mesh_set = []
            for child in obj.get('children', []):
                if child.get('type') == 'MESH':
                    mesh_set.append({'name': child['name'], 'visible': True})

            # Build behavior
            behavior = _create_text_behavior(
                name=obj.get('hvym_mesh_interaction_name', ''),
                use_method=False,
                method=obj.get('hvym_mesh_interaction_call', ''),
                behavior_type=obj.get('hvym_interactable_behavior', 'NONE'),
                use_behavior=False,
            )
            if obj.get('hvym_interactable_behavior', 'NONE') != 'NONE':
                behavior['use_method'] = True
                behavior['use_behavior'] = True

            # Build interactable
            interactable = InteractableDataClass(
                interactable=obj.get('hvym_interactable', False),
                has_return=obj.get('hvym_interactable_has_return', False),
                interaction_type=obj.get('hvym_mesh_interaction_type', ''),
                selector_dir=obj.get('hvym_interactable_selector_dir', ''),
                name=obj.get('hvym_mesh_interaction_name', ''),
                call=obj.get('hvym_mesh_interaction_call', ''),
                default_text=obj.get('hvym_mesh_interaction_default_text', ''),
                text_scale=obj.get('hvym_mesh_interaction_text_scale', 1.0),
                text_wrap=obj.get('hvym_mesh_interaction_text_wrap', False),
                param_type=obj.get('hvym_mesh_interaction_param_type', ''),
                slider_param_type=obj.get('hvym_mesh_interaction_slider_param_type', ''),
                toggle_param_type=obj.get('hvym_mesh_interaction_toggle_param_type', ''),
                string_param=obj.get('hvym_mesh_interaction_string_param', ''),
                int_param=obj.get('hvym_mesh_interaction_int_param', 0),
                float_default=obj.get('hvym_mesh_interaction_float_default', 0.0),
                float_min=obj.get('hvym_mesh_interaction_float_min', 0.0),
                float_max=obj.get('hvym_mesh_interaction_float_max', 1.0),
                int_default=obj.get('hvym_mesh_interaction_int_default', 0),
                int_min=obj.get('hvym_mesh_interaction_int_min', 0),
                int_max=obj.get('hvym_mesh_interaction_int_max', 100),
                toggle_state=obj.get('hvym_mesh_interaction_toggle_state', False),
                toggle_int=obj.get('hvym_mesh_interaction_toggle_int', 0),
                mesh_set=mesh_set,
                behavior=behavior,
            ).dictionary

            data[obj['name']] = interactable

    return data
