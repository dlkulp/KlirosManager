import { MetadataDto } from "@/types/api-client";

export const colors = {
    red: "#980000",
    blue: "#304ffe",
    purple: "#aa00ff",
    green: "#00c858",
    gold: "#ffab00"
};

export function getAttribution(metaData: MetadataDto | null) {
  if (metaData?.Composer)
    return `By ${metaData.Composer}`;
  else if (metaData?.Arranger)
    return `Arr. ${metaData.Arranger}`;
  else
    return "Unknown Composer";
}

/**
 * @param date Date to check
 * @param range {startDate: "11/15", endDate: "12/24"}
 * @returns
 */
export function isDateInRange(date: Date, range: {start: string | Date, end: string | Date}): boolean {
    if (range.start instanceof Date && range.end instanceof Date)
        return date >= range.start && date <= range.end;
  else if (
    (typeof range.start === "string" || range.start instanceof String) &&
    (typeof range.end === "string" || range.end instanceof String)) {
    if (Number(range.start.split("/")[0])>Number(range.end.split("/")[0]))
      // If the start month is greater than the end month, it means the range spans across the year-end.
      // In this case, we need to check if the date is either after the start date or before the end date.
      return date >= new Date(range.start) && date <= new Date(range.end);
    else return date >= new Date(range.start) && date <= new Date(range.end);
  }
  throw new Error("Types of range.start and range.end must be either both Date objects or both strings.");
}

/**
 * @param year Which year to calculate Pascha for
 * @returns Date of Pascha in a given year
 */
export function getPascha(year: number): Date {
  const a = year % 4;
  const b = year % 7;
  const c = year % 19;
  const d = (19 * c + 15) % 30;
  const e = (2 * a + 4 * b - d + 34) % 7;
  const month = Math.floor((d + e + 114) / 31);
  const day = ((d + e + 114) % 31) + 1;
  return new Date(year, month - 1, day + 13); // Adjust for the Julian to Gregorian calendar difference
}

/**
 * @param year The year to calculate the range of lent for
 * @returns An object containing the start and end dates of lent for a given year
 */
export function getLentRange(year: number = new Date().getFullYear()) {
  const pascha = getPascha(year);
  const lentStart = new Date(pascha);
  lentStart.setDate(pascha.getDate() - 48); // 48 days before Pascha
  const lentEnd = new Date(pascha);
  lentEnd.setDate(pascha.getDate() - 1); // 1 day before Pascha
  return { start: lentStart, end: lentEnd };
}

export function getPalmSundayRange(year: number = new Date().getFullYear()) {
  const pascha = getPascha(year);
  const palmSundayStart = new Date(pascha);
  palmSundayStart.setDate(pascha.getDate() - 8); // 8 days before Pascha to include Lazarus Saturday
  const palmSundayEnd = new Date(pascha);
  palmSundayEnd.setDate(pascha.getDate() - 7); // End on Palm Sunday, which is 7 days before Pascha
  return { start: palmSundayStart, end: palmSundayEnd };
}

/**
 * @param year The year to calculate the range of paschaltide for
 * @returns An object containing the start and end dates of paschaltide for a given year
 */
export function getPaschaltideRange(year: number = new Date().getFullYear()) {
  const pascha = getPascha(year);
  const paschaltideStart = new Date(pascha);
  const paschaltideEnd = new Date(pascha);
  paschaltideEnd.setDate(pascha.getDate() + 48); // 48 days after Pascha
  return { start: paschaltideStart, end: paschaltideEnd };
}

export function getPentecostRange(year: number = new Date().getFullYear()) {
  const pascha = getPascha(year);
  const pentecostStart = new Date(pascha);
  pentecostStart.setDate(pascha.getDate() + 49); // 49 days after Pascha
  const pentecostEnd = new Date(pascha);
  pentecostEnd.setDate(pascha.getDate() + 55); // 55 days after Pascha
  return { start: pentecostStart, end: pentecostEnd };
}

/**
 * @param date Date to strip year from
 * @returns "month/day" string
 */
export function dateStripYear(date: Date): string {
  return `${date.getMonth() + 1}/${date.getDate()}`;
}
