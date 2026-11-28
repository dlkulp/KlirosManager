import type {
  ImportCreatedResponseDto as HandoffCreated,
  ResourceWithMetadataDto as HandoffResource,
  KlirosApi as HandoffApi,
  FlagReportDto as HandoffFlagReport,
  PendingFlagReportsResponseDto,
  ResolveFlagReportRequestDto,
} from "../.specs/api-client";
import type {
  ImportCreatedResponseDto as FrontendCreated,
  ResourceWithMetadataDto as FrontendResource,
  KlirosApi as FrontendApi,
  FlagReportDto as FrontendFlagReport,
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

export type FlagReportContractAssertions = [
  Assert<Equal<HandoffFlagReport, FrontendFlagReport>>,
  Assert<Equal<HandoffFlagReport["UserID"], number | null>>,
  Assert<Equal<ReturnType<HandoffApi["reportResource"]>, Promise<{ flag_report_id: number }>>>,
  Assert<Equal<ReturnType<FrontendApi["getPendingFlagReports"]>, Promise<PendingFlagReportsResponseDto>>>,
  Assert<Equal<Parameters<HandoffApi["resolveFlagReport"]>[1], ResolveFlagReportRequestDto>>,
  Assert<Equal<ResolveFlagReportRequestDto["is_sustained"], boolean>>,
];
