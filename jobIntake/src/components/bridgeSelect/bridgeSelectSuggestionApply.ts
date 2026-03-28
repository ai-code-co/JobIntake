import type { MappedSuggestions, SuggestibleFieldKey } from "../jobIntakeTypes";
import {
  AI_FORCE_OVERWRITE_FIELDS,
  BRIDGESELECT_SUGGESTION_FIELDS,
  FILE_FIELD_NAMES,
  LEGACY_IGNORED_SUGGESTION_FIELDS,
} from "../jobIntakeSuggestionConfig";
import type { BridgeSelectFormState, BridgeSelectSuggestibleFieldKey } from "./bridgeSelectTypes";

function bridgeSelectSuggestionValueUnchanged(current: unknown, suggested: unknown): boolean {
  if (typeof suggested === "string" && typeof current === "string") {
    return current.trim() === suggested.trim();
  }
  if (typeof suggested === "boolean" && typeof current === "boolean") {
    return current === suggested;
  }
  return false;
}

export function applyMappedSuggestionsToBridgeSelectForm(
  form: BridgeSelectFormState,
  mappedSuggestions: MappedSuggestions,
  touchedFields: Set<keyof BridgeSelectFormState>,
): { nextForm: BridgeSelectFormState; appliedKeys: Set<BridgeSelectSuggestibleFieldKey> } {
  const nextForm = { ...form };
  const appliedKeys = new Set<BridgeSelectSuggestibleFieldKey>();
  const mappedEntries = Object.entries(mappedSuggestions as Record<string, unknown>);

  for (const [rawKey, rawValue] of mappedEntries) {
    if (LEGACY_IGNORED_SUGGESTION_FIELDS.has(rawKey)) {
      continue;
    }
    if (!(rawKey in nextForm) || FILE_FIELD_NAMES.includes(rawKey as (typeof FILE_FIELD_NAMES)[number])) {
      continue;
    }
    const key = rawKey as SuggestibleFieldKey;
    if (!BRIDGESELECT_SUGGESTION_FIELDS.has(key)) continue;
    const value = rawValue as BridgeSelectFormState[BridgeSelectSuggestibleFieldKey];
    if (typeof value === "undefined" || value === null) continue;
    const currentValue = form[key as BridgeSelectSuggestibleFieldKey];
    const isStringField = typeof value === "string";
    const shouldForceOverwrite = AI_FORCE_OVERWRITE_FIELDS.has(key);
    const isEmptyStringField = isStringField && typeof currentValue === "string" && !currentValue.trim();
    const isUntouchedBooleanField = typeof value === "boolean" && !touchedFields.has(key as keyof BridgeSelectFormState);
    const isForceOverwriteStringField = shouldForceOverwrite && isStringField && Boolean(value.trim());
    const isForceOverwriteBooleanField = shouldForceOverwrite && typeof value === "boolean";

    if (
      isEmptyStringField ||
      isUntouchedBooleanField ||
      isForceOverwriteStringField ||
      isForceOverwriteBooleanField
    ) {
      if (bridgeSelectSuggestionValueUnchanged(currentValue, value)) {
        continue;
      }
      (nextForm as Record<string, unknown>)[rawKey] = value;
      appliedKeys.add(key as BridgeSelectSuggestibleFieldKey);
    }
  }

  return { nextForm, appliedKeys };
}
