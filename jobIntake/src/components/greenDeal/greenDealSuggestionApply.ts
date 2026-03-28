import type { MappedSuggestions, SuggestibleFieldKey } from "../jobIntakeTypes";
import {
  AI_FORCE_OVERWRITE_FIELDS,
  FILE_FIELD_NAMES,
  GREENDEAL_EXCLUDED_FIELDS,
  LEGACY_IGNORED_SUGGESTION_FIELDS,
} from "../jobIntakeSuggestionConfig";
import type { GreenDealFormState, GreenDealSuggestibleFieldKey } from "./greenDealTypes";

export function applyMappedSuggestionsToGreenDealForm(
  form: GreenDealFormState,
  mappedSuggestions: MappedSuggestions,
  touchedFields: Set<keyof GreenDealFormState>,
): { nextForm: GreenDealFormState; appliedKeys: Set<GreenDealSuggestibleFieldKey> } {
  const nextForm = { ...form };
  const appliedKeys = new Set<GreenDealSuggestibleFieldKey>();
  const mappedEntries = Object.entries(mappedSuggestions as Record<string, unknown>);

  for (const [rawKey, rawValue] of mappedEntries) {
    if (LEGACY_IGNORED_SUGGESTION_FIELDS.has(rawKey)) {
      continue;
    }
    if (!(rawKey in nextForm) || FILE_FIELD_NAMES.includes(rawKey as (typeof FILE_FIELD_NAMES)[number])) {
      continue;
    }
    const key = rawKey as SuggestibleFieldKey;
    if (GREENDEAL_EXCLUDED_FIELDS.has(key)) continue;
    const value = rawValue as GreenDealFormState[GreenDealSuggestibleFieldKey];
    if (typeof value === "undefined" || value === null) continue;
    const currentValue = form[key as GreenDealSuggestibleFieldKey];
    const isStringField = typeof value === "string";
    const shouldForceOverwrite = AI_FORCE_OVERWRITE_FIELDS.has(key);
    const isEmptyStringField = isStringField && typeof currentValue === "string" && !currentValue.trim();
    const isUntouchedBooleanField = typeof value === "boolean" && !touchedFields.has(key as keyof GreenDealFormState);
    const isForceOverwriteStringField = shouldForceOverwrite && isStringField && Boolean(value.trim());
    const isForceOverwriteBooleanField = shouldForceOverwrite && typeof value === "boolean";

    if (
      isEmptyStringField ||
      isUntouchedBooleanField ||
      isForceOverwriteStringField ||
      isForceOverwriteBooleanField
    ) {
      (nextForm as Record<string, unknown>)[rawKey] = value;
      appliedKeys.add(key as GreenDealSuggestibleFieldKey);
    }
  }

  return { nextForm, appliedKeys };
}
