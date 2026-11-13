import { AnyARecord } from "dns"

export type Score = {
  "DisplayName": string,
  "FileHash": string,
  "GroupID": string,
  "Hidden": boolean,
  "MetaData": Record<string, any>,
  "OriginalName": string,
  "Public": boolean,
  "Reviewed": boolean,
  "Source": string,
  "UserID": number,
  "VisualHash": string,
  "api_url": string,
  "detail_url": string,
  "id": number,
  "thumbnail_sizes": string,
  "thumbnail_srcset": string,
  "thumbnail_url": string,
  "title": string
}
