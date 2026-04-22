(function () {
  const STORAGE_KEY = "laminate_tool_custom_materials_v1";
  const LAST_ANALYSIS_KEY = "laminate_tool_last_analysis_v1";
  const EXPORT_FORMAT = "laminate-tool.custom-material-library";
  const EXPORT_VERSION = 1;
  const RESERVED_IDS = new Set(["Dummy"]);
  const ALLOWED_CATEGORIES = new Set(["fiber", "core"]);
  const ALLOWED_FIBER_FAMILIES = new Set(["twill", "ud"]);

  const POSITIVE_NUMERIC_FIELDS = ["e1_pa", "e2_pa", "g12_pa", "thickness_mm"];
  const MANDATORY_FINITE_NUMERIC_FIELDS = ["poisson_input"];
  const OPTIONAL_FINITE_NUMERIC_FIELDS = [
    "strength_x",
    "strength_x_compression",
    "strength_y",
    "strength_y_compression",
    "strength_s",
  ];

  const normalizeText = (value) => String(value ?? "").trim();

  const sortMaterialsByName = (materials) =>
    [...materials].sort((left, right) => {
      const leftName = normalizeText(left?.name).toLocaleLowerCase("es");
      const rightName = normalizeText(right?.name).toLocaleLowerCase("es");
      if (leftName === rightName) {
        return normalizeText(left?.id).localeCompare(normalizeText(right?.id), "es");
      }
      return leftName.localeCompare(rightName, "es");
    });

  const parsePositiveNumber = (value, fieldName, materialId) => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      throw new Error(`El material '${materialId}' usa un valor no válido en '${fieldName}'.`);
    }
    return parsed;
  };

  const parseFiniteNumber = (value, fieldName, materialId, { fallback } = {}) => {
    const hasFallback = fallback !== undefined;
    const candidate =
      value === undefined || value === null || value === ""
        ? hasFallback
          ? fallback
          : value
        : value;
    const parsed = Number(candidate);
    if (!Number.isFinite(parsed)) {
      throw new Error(`El material '${materialId}' usa un valor no válido en '${fieldName}'.`);
    }
    return parsed;
  };

  const canonicalizeMaterial = (payload, { legacy = false } = {}) => {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("El archivo contiene un material con un formato no válido.");
    }

    const id = normalizeText(payload.id);
    const name = normalizeText(payload.name);
    if (!id || !name) {
      throw new Error("Todos los materiales importados deben tener ID y nombre.");
    }
    if (RESERVED_IDS.has(id)) {
      throw new Error(`El identificador '${id}' está reservado y no se puede importar.`);
    }

    const category = normalizeText(payload.material_category || "fiber").toLowerCase();
    if (!ALLOWED_CATEGORIES.has(category)) {
      throw new Error(`El material '${id}' usa una categoría no compatible.`);
    }

    let fiberFamily = null;
    if (category === "fiber") {
      const defaultFamily = legacy ? "twill" : "";
      fiberFamily = normalizeText(payload.fiber_family || defaultFamily).toLowerCase();
      if (!ALLOWED_FIBER_FAMILIES.has(fiberFamily)) {
        throw new Error(`El material '${id}' debe indicar si es fibra twill o UD.`);
      }
    }

    const material = {
      id,
      name,
      material_category: category,
      fiber_family: category === "fiber" ? fiberFamily : null,
      user_selectable: true,
      notes: normalizeText(payload.notes) || "Imported custom material.",
    };

    POSITIVE_NUMERIC_FIELDS.forEach((fieldName) => {
      material[fieldName] = parsePositiveNumber(payload[fieldName], fieldName, id);
    });
    MANDATORY_FINITE_NUMERIC_FIELDS.forEach((fieldName) => {
      material[fieldName] = parseFiniteNumber(payload[fieldName], fieldName, id);
    });
    OPTIONAL_FINITE_NUMERIC_FIELDS.forEach((fieldName) => {
      material[fieldName] = parseFiniteNumber(payload[fieldName], fieldName, id, { fallback: 0 });
    });

    return material;
  };

  const canonicalizeStoredMaterials = (payload) => {
    if (!Array.isArray(payload)) {
      return [];
    }
    const materials = [];
    payload.forEach((material) => {
      try {
        materials.push(canonicalizeMaterial(material, { legacy: true }));
      } catch {
        return;
      }
    });
    return sortMaterialsByName(materials);
  };

  const loadStoredMaterials = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return [];
      }
      return canonicalizeStoredMaterials(JSON.parse(raw));
    } catch {
      return [];
    }
  };

  const saveStoredMaterials = (materials) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sortMaterialsByName(materials)));
  };

  const buildExportPayload = (materials) =>
    JSON.stringify(
      {
        format: EXPORT_FORMAT,
        version: EXPORT_VERSION,
        exported_at: new Date().toISOString(),
        materials: sortMaterialsByName(materials),
      },
      null,
      2
    );

  const parseImportPayload = (rawText) => {
    const text = String(rawText ?? "").trim();
    if (!text) {
      throw new Error("El archivo está vacío.");
    }

    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch {
      throw new Error("No se ha podido leer el archivo JSON.");
    }

    let materialsPayload;
    let importMeta;
    if (Array.isArray(parsed)) {
      materialsPayload = parsed;
      importMeta = {
        format: "legacy-array",
        version: 0,
        exported_at: null,
      };
    } else if (parsed?.format === EXPORT_FORMAT && parsed?.version === EXPORT_VERSION && Array.isArray(parsed?.materials)) {
      materialsPayload = parsed.materials;
      importMeta = {
        format: parsed.format,
        version: parsed.version,
        exported_at: parsed.exported_at || null,
      };
    } else if (parsed?.format === EXPORT_FORMAT && Number(parsed?.version) > EXPORT_VERSION) {
      throw new Error("El archivo usa una versión de biblioteca más reciente y no es compatible todavía.");
    } else {
      throw new Error("El archivo no contiene una biblioteca de materiales compatible.");
    }

    const seenIds = new Set();
    const materials = materialsPayload.map((material) => {
      const normalized = canonicalizeMaterial(material, { legacy: importMeta.version === 0 });
      if (seenIds.has(normalized.id)) {
        throw new Error("El archivo contiene IDs repetidos y no se puede importar de forma segura.");
      }
      seenIds.add(normalized.id);
      return normalized;
    });

    return {
      importMeta,
      materials: sortMaterialsByName(materials),
    };
  };

  const analyzeImport = ({ currentMaterials, importedMaterials, baseMaterialIds }) => {
    const currentIds = new Set(currentMaterials.map((material) => material.id));
    const baseIds = new Set(baseMaterialIds || []);
    const newMaterials = [];
    const customConflicts = [];
    const baseOverrides = [];

    importedMaterials.forEach((material) => {
      if (currentIds.has(material.id)) {
        customConflicts.push(material);
        return;
      }
      if (baseIds.has(material.id)) {
        baseOverrides.push(material);
        return;
      }
      newMaterials.push(material);
    });

    return {
      total: importedMaterials.length,
      newMaterials,
      customConflicts,
      baseOverrides,
    };
  };

  const mergeMaterials = (currentMaterials, importedMaterials) => {
    const merged = new Map();
    currentMaterials.forEach((material) => {
      merged.set(material.id, material);
    });
    importedMaterials.forEach((material) => {
      merged.set(material.id, material);
    });
    return sortMaterialsByName([...merged.values()]);
  };

  const collectReferencedMaterialIds = (entry) => {
    const formState = entry?.form_state;
    const referencedIds = new Set();
    if (!formState) {
      return referencedIds;
    }

    (formState.layers || []).forEach((layer) => {
      if (layer?.material_id) {
        referencedIds.add(layer.material_id);
      }
    });
    (formState.bottom_layers || []).forEach((layer) => {
      if (layer?.material_id) {
        referencedIds.add(layer.material_id);
      }
    });
    if (formState.core_material_id) {
      referencedIds.add(formState.core_material_id);
    }
    return referencedIds;
  };

  const reconcileLastAnalysis = ({ currentMaterials, baseMaterialIds }) => {
    try {
      const raw = localStorage.getItem(LAST_ANALYSIS_KEY);
      if (!raw) {
        return;
      }
      const entry = JSON.parse(raw);
      const referencedIds = collectReferencedMaterialIds(entry);
      const availableIds = new Set([
        ...(baseMaterialIds || []),
        ...currentMaterials.map((material) => material.id),
      ]);

      const isStillValid = [...referencedIds].every((materialId) => availableIds.has(materialId));
      if (!isStillValid) {
        localStorage.removeItem(LAST_ANALYSIS_KEY);
        return;
      }

      if (entry?.form_state) {
        entry.form_state.custom_materials = currentMaterials.filter((material) =>
          referencedIds.has(material.id)
        );
        localStorage.setItem(LAST_ANALYSIS_KEY, JSON.stringify(entry));
      }
    } catch {
      localStorage.removeItem(LAST_ANALYSIS_KEY);
    }
  };

  window.LaminateMaterialCatalog = {
    STORAGE_KEY,
    LAST_ANALYSIS_KEY,
    EXPORT_FORMAT,
    EXPORT_VERSION,
    loadStoredMaterials,
    saveStoredMaterials,
    buildExportPayload,
    parseImportPayload,
    analyzeImport,
    mergeMaterials,
    reconcileLastAnalysis,
    sortMaterialsByName,
  };
})();
