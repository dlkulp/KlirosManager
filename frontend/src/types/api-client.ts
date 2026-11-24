export type MetadataDto = Record<string, string>;
export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

export interface UserDto {
  UserID: number;
  Name: string;
  Email: string;
  JoinedAt: string;
  UserType: UserTypeDto;
}
export type UserTypeDto = "regular" | "moderator" | "admin";

export type SessionResponseDto =
  | { logged_in: true; user: UserDto }
  | { logged_in: false; user: null };
export type LoginResponseDto = Extract<SessionResponseDto, { logged_in: true }>;
export type LogoutResponseDto = Extract<SessionResponseDto, { logged_in: false }>;

export interface ResourceDto {
  id: number;
  DisplayName: string | null;
  OriginalName: string;
  GroupID: number | null;
  Source: string | null;
  UserID: number;
  Reviewed: boolean | null;
  ReviewerId: number | null;
  ReviewedAt: string | null;
  Public: boolean | null;
  Deleted: boolean | null;
  VisualHash: string | null;
  FileHash: string | null;
  DownloadCount?: number | null;
  title: string;
  thumbnail_url: string | null;
  thumbnail_srcset: string | null;
  thumbnail_sizes: string;
  detail_url: string;
  api_url: string;
}

export interface LatestResponseDto { recent_works: ResourceDto[] }
export interface LibraryResponseDto { works: ResourceDto[] }

export type SearchSort = "uploaded" | "popularity" | "name";
export type SearchPageSize = 24 | 48 | 96;
export interface SearchRequestDto {
  q?: string;
  filters?: Record<string, string>;
  page?: number;
  page_size?: SearchPageSize;
  sort?: SearchSort;
}
export interface SearchResourceDto extends ResourceDto {
  metadata: MetadataDto;
  uploaded_at: number;
  popularity: number;
}
export interface SearchResponseDto {
  results: SearchResourceDto[];
  total: number;
  page: number;
  page_size: SearchPageSize;
  page_count: number;
}
export interface SearchFacetsResponseDto { facets: Record<string, string[]> }

export interface CollectionDto {
  id: number;
  Name: string;
  Public: boolean | null;
  UserId: number | null;
  CreationDate: string | null;
}
export interface ProfileCollectionDto extends CollectionDto { items: ResourceDto[] }
export interface PublicProfileResponseDto {
  user: Omit<UserDto, "Email">;
  initials: string;
  uploads: ResourceDto[];
}
export interface ProfileResponseDto extends PublicProfileResponseDto {
  user: UserDto;
  favorites: ResourceDto[];
  collections: ProfileCollectionDto[];
}
export interface UpdateProfileRequestDto { name: string }
export interface UpdateProfileResponseDto { user: UserDto }

export interface MetadataDefinitionDto {
  id: number;
  Name: string;
  Type: string;
  Options: string[] | null;
  Core: boolean | null;
  Extracted: boolean | null;
  Searchable: boolean | null;
  Required?: boolean;
}
export interface MetadataFieldDto extends MetadataDefinitionDto { value: string }
export interface SiteMetadataResponseDto {
  metadata_fields: MetadataDefinitionDto[];
}
export interface OcrDto {
  status: "success" | "unavailable" | "error";
  text: string;
  message: string;
}
export interface UploaderDto {
  Name: string;
  JoinedAt: string;
  UserID?: number;
  UserType?: UserTypeDto;
}
export interface ResourceDetailResponseDto {
  resource: ResourceDto;
  original_name: string;
  uploader: UploaderDto;
  uploader_initials: string;
  is_favorite: boolean;
  ocr: Partial<OcrDto>;
  metadata: MetadataDto;
  file_url: string;
  download_url: string;
}

export interface UpdateResourceRequestDto {
  DisplayName: string;
  metadata?: Record<string, JsonValue>;
}
export interface RankedMatchDto {
  resource_id: number;
  title: string | null;
  original_name: string;
  composer: string | null;
  hamming_distance: number | null;
  title_similarity: number | null;
  composer_similarity: number | null;
  confidence: number;
  detail_url: string;
  preview_url: string;
}
export interface UpdateResourceResponseDto {
  status: "updated";
  resource_id: number;
  title: string;
  detail_url: string;
  matches: RankedMatchDto[];
  import_complete: boolean;
}
export interface DeleteResourceResponseDto { deleted: true; resource_id: number }
export interface FavoriteResponseDto { is_favorite: boolean }
export type UnfavoriteResponseDto = { is_favorite: false };

export type ResourceCollectionRequestDto =
  | { collection_id: number; action?: "add" | "remove"; new_collection_name?: never }
  | { new_collection_name: string; action?: "add"; collection_id?: never };
export interface ResourceCollectionResponseDto {
  collection: string;
  collection_id: number;
  is_public: boolean;
  added: boolean;
  changed: boolean;
}
export interface RenameCollectionRequestDto { name: string }
export interface RenameCollectionResponseDto { collection: CollectionDto }
export interface DeleteCollectionResponseDto { deleted: true; collection_id: number }
export interface RemoveCollectionItemResponseDto { removed: boolean; resource_id: number }
export interface UpdateUserTypeRequestDto { user_type: Exclude<UserTypeDto, "admin"> }
export interface UpdateUserTypeResponseDto { user_id: number; user_type: Exclude<UserTypeDto, "admin"> }

export interface ImportCheckRequestDto { file: Blob; filename: string }
export interface ImportDebugDto {
  file_hash: string | null;
  visual_hash: string | null;
  ocr_text: string;
}
export interface ImportMatchDto {
  resource_id: number;
  original_name: string;
  visual_hash: string;
  hamming_distance: number;
}
export interface InferredMetadataValueDto {
  value: string;
  source: "ocr";
  reviewed: false;
}
export interface ImportCreatedResponseDto {
  status: "created";
  upload: {
    resource_id: number;
    stored_name: string;
    original_name: string;
    title: string;
    source: string;
    thumbnail_url: string;
    thumbnail_600_url: string;
    thumbnail_srcset: string;
    detail_url: string;
  };
  ocr: OcrDto;
  visual_hash: string | null;
  matches: ImportMatchDto[];
  inferred_metadata: Record<string, InferredMetadataValueDto>;
  debug: ImportDebugDto;
  errors: string[];
}
export interface ImportDuplicateResponseDto {
  status: "duplicate";
  match_type: "sha256" | "phash";
  duplicate: {
    resource_id: number;
    title: string;
    original_name: string;
    detail_url: string;
  };
  debug: ImportDebugDto;
}
export interface ImportRejectedResponseDto {
  status: "rejected";
  reason: "not_sheet_music";
  error: string;
  debug: ImportDebugDto;
  reference_check: { hamming_distance: number; reference_image: string; threshold: number };
}
export type ImportCheckResponseDto = ImportCreatedResponseDto | ImportDuplicateResponseDto | ImportRejectedResponseDto;
export interface ApiErrorResponseDto { error: string; status?: "error" }
export interface BinaryResponseDto {
  body: Blob;
  content_type: string | null;
  content_disposition: string | null;
}
export type ThumbnailHeight = 300 | 600;
export interface ApiRequestOptions { signal?: AbortSignal }
export interface KlirosApiOptions {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
  credentials?: RequestCredentials;
}

export class ApiError extends Error {
  constructor(message: string, public readonly status: number, public readonly body: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

export class KlirosApi {
  private readonly baseUrl: string;
  private readonly fetcher: typeof globalThis.fetch;
  private readonly credentials: RequestCredentials;

  constructor(options: KlirosApiOptions = {}) {
    this.baseUrl = (options.baseUrl || "").replace(/\/+$/, "");
    this.fetcher = options.fetch || globalThis.fetch.bind(globalThis);
    this.credentials = options.credentials || "include";
  }

  private async request(path: string, init: RequestInit): Promise<Response> {
    return this.fetcher(`${this.baseUrl}${path}`, { ...init, credentials: this.credentials });
  }

  private async error(response: Response): Promise<ApiError> {
    const text = await response.text();
    let body: unknown = text;
    try { body = JSON.parse(text); } catch { body = text; }
    const message = typeof body === "object" && body !== null && "error" in body && typeof body.error === "string"
      ? body.error : `HTTP ${response.status} ${response.statusText}`.trim();
    return new ApiError(message, response.status, body);
  }

  private async json<ResponseDto>(path: string, init: RequestInit = {}): Promise<ResponseDto> {
    const response = await this.request(path, init);
    if (!response.ok) throw await this.error(response);
    const text = await response.text();
    try { return JSON.parse(text) as ResponseDto; }
    catch { throw new ApiError("Expected a JSON response.", response.status, text); }
  }

  private jsonBody(body: unknown, method: "POST" | "PATCH", options: ApiRequestOptions): RequestInit {
    return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: options.signal };
  }

  getSession(options: ApiRequestOptions = {}): Promise<SessionResponseDto> {
    return this.json("/api/session", options);
  }
  login(options: ApiRequestOptions = {}): Promise<LoginResponseDto> {
    return this.json("/api/login", { method: "POST", ...options });
  }
  logout(options: ApiRequestOptions = {}): Promise<LogoutResponseDto> {
    return this.json("/api/logout", { method: "POST", ...options });
  }
  getLatest(count?: number, options: ApiRequestOptions = {}): Promise<LatestResponseDto> {
    const suffix = count === undefined ? "" : `/${count}`;
    return this.json(`/api/latest${suffix}`, options);
  }
  getLibrary(options: ApiRequestOptions = {}): Promise<LibraryResponseDto> {
    return this.json("/api/library", options);
  }
  search(request: SearchRequestDto = {}, options: ApiRequestOptions = {}): Promise<SearchResponseDto> {
    const query = new URLSearchParams();
    if (request.q !== undefined) query.set("q", request.q);
    if (request.filters !== undefined) query.set("filters", JSON.stringify(request.filters));
    if (request.page !== undefined) query.set("page", String(request.page));
    if (request.page_size !== undefined) query.set("page_size", String(request.page_size));
    if (request.sort !== undefined) query.set("sort", request.sort);
    return this.json(`/api/search?${query}`, options);
  }
  getSearchFacets(options: ApiRequestOptions = {}): Promise<SearchFacetsResponseDto> {
    return this.json("/api/search/facets", options);
  }
  getSiteMetadata(options: ApiRequestOptions = {}): Promise<SiteMetadataResponseDto> {
    return this.json("/api/site/metadata", options);
  }
  getProfile(options?: ApiRequestOptions): Promise<ProfileResponseDto>;
  getProfile(userId: number, options?: ApiRequestOptions): Promise<PublicProfileResponseDto | ProfileResponseDto>;
  getProfile(
    userIdOrOptions: number | ApiRequestOptions = {},
    options: ApiRequestOptions = {},
  ): Promise<PublicProfileResponseDto | ProfileResponseDto> {
    if (typeof userIdOrOptions === "number") {
      return this.json(`/api/profile/${userIdOrOptions}`, options);
    }
    return this.json("/api/profile", userIdOrOptions);
  }
  updateProfile(request: UpdateProfileRequestDto, options: ApiRequestOptions = {}): Promise<UpdateProfileResponseDto> {
    return this.json("/api/profile", this.jsonBody(request, "PATCH", options));
  }
  updateUserType(userId: number, request: UpdateUserTypeRequestDto, options: ApiRequestOptions = {}): Promise<UpdateUserTypeResponseDto> {
    return this.json(`/api/admin/users/${userId}/type`, this.jsonBody(request, "PATCH", options));
  }
  getResource(resourceId: number, options: ApiRequestOptions = {}): Promise<ResourceDetailResponseDto> {
    return this.json(`/api/library/${resourceId}`, options);
  }
  updateResource(resourceId: number, request: UpdateResourceRequestDto, options: ApiRequestOptions = {}): Promise<UpdateResourceResponseDto> {
    return this.json(`/api/library/${resourceId}`, this.jsonBody(request, "PATCH", options));
  }
  deleteResource(resourceId: number, options: ApiRequestOptions = {}): Promise<DeleteResourceResponseDto> {
    return this.json(`/api/library/${resourceId}`, { method: "DELETE", ...options });
  }
  toggleFavorite(resourceId: number, options: ApiRequestOptions = {}): Promise<FavoriteResponseDto> {
    return this.json(`/api/library/${resourceId}/favorite`, { method: "POST", ...options });
  }
  unfavorite(resourceId: number, options: ApiRequestOptions = {}): Promise<UnfavoriteResponseDto> {
    return this.json(`/api/library/${resourceId}/favorite`, { method: "DELETE", ...options });
  }
  saveResourceCollection(resourceId: number, request: ResourceCollectionRequestDto, options: ApiRequestOptions = {}): Promise<ResourceCollectionResponseDto> {
    return this.json(`/api/library/${resourceId}/collections`, this.jsonBody(request, "POST", options));
  }
  renameCollection(collectionId: number, request: RenameCollectionRequestDto, options: ApiRequestOptions = {}): Promise<RenameCollectionResponseDto> {
    return this.json(`/api/profile/collections/${collectionId}`, this.jsonBody(request, "PATCH", options));
  }
  deleteCollection(collectionId: number, options: ApiRequestOptions = {}): Promise<DeleteCollectionResponseDto> {
    return this.json(`/api/profile/collections/${collectionId}`, { method: "DELETE", ...options });
  }
  removeCollectionItem(collectionId: number, resourceId: number, options: ApiRequestOptions = {}): Promise<RemoveCollectionItemResponseDto> {
    return this.json(`/api/profile/collections/${collectionId}/items/${resourceId}`, { method: "DELETE", ...options });
  }
  async checkImport(request: ImportCheckRequestDto, options: ApiRequestOptions = {}): Promise<ImportCheckResponseDto> {
    const form = new FormData();
    form.append("file", request.file, request.filename);
    const response = await this.request("/api/library/import/check", { method: "POST", body: form, ...options });
    if (response.status === 422) {
      const text = await response.text();
      let body: unknown;
      try { body = JSON.parse(text); }
      catch { throw new ApiError("Unexpected import rejection response.", response.status, text); }
      if (typeof body === "object" && body !== null && "status" in body && body.status === "rejected") {
        return body as ImportRejectedResponseDto;
      }
      throw new ApiError("Unexpected import rejection response.", response.status, body);
    }
    if (!response.ok) throw await this.error(response);
    const text = await response.text();
    try { return JSON.parse(text) as ImportCreatedResponseDto | ImportDuplicateResponseDto; }
    catch { throw new ApiError("Expected a JSON response.", response.status, text); }
  }
  private async binary(path: string, options: ApiRequestOptions): Promise<BinaryResponseDto> {
    const response = await this.request(path, options);
    if (!response.ok) throw await this.error(response);
    return {
      body: await response.blob(),
      content_type: response.headers.get("Content-Type"),
      content_disposition: response.headers.get("Content-Disposition"),
    };
  }
  getFile(resourceId: number, options: ApiRequestOptions = {}): Promise<BinaryResponseDto> {
    return this.binary(`/api/library/${resourceId}/file`, options);
  }
  downloadResource(resourceId: number, options: ApiRequestOptions = {}): Promise<BinaryResponseDto> {
    return this.binary(`/api/library/${resourceId}/download`, options);
  }
  getThumbnail(resourceId: number, height?: ThumbnailHeight, options: ApiRequestOptions = {}): Promise<BinaryResponseDto> {
    const suffix = height === undefined ? "" : `/${height}`;
    return this.binary(`/api/library/${resourceId}/thumbnail${suffix}`, options);
  }
}