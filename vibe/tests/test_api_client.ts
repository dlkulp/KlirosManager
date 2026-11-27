import type {
  ImportCreatedResponseDto as HandoffCreated,
  ResourceWithMetadataDto as HandoffResource,
} from "../.specs/api-client";
import type {
  ImportCreatedResponseDto as FrontendCreated,
  ResourceWithMetadataDto as FrontendResource,
} from "../../frontend/src/types/api-client";

type Assert<T extends true> = T;
type Equal<A, B> =
  (<T>() => T extends A ? 1 : 2) extends (<T>() => T extends B ? 1 : 2) ? true : false;
type CreatedFields = "status" | "upload" | "matches" | "debug" | "errors";

export type ImportCreatedContractAssertions = [
  Assert<Equal<keyof HandoffCreated, CreatedFields>>,
  Assert<Equal<HandoffCreated["upload"], HandoffResource>>,
  Assert<Equal<keyof FrontendCreated, CreatedFields>>,
  Assert<Equal<FrontendCreated["upload"], FrontendResource>>,
];
