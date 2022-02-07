import { ref, customRef } from "vue";
import queryString from "query-string";

export const debounce = (fn: Function, delay = 1000, immediate = false) => {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: any[]) => {
    if (immediate && !timeout) fn(...args);
    clearTimeout(timeout);

    timeout = setTimeout(() => {
      fn(...args);
    }, delay);
  }
} 

export function debouncedRef(initialValue: any, delay: number = 750, immediate: boolean = false) {
	const state = ref(initialValue);
	const debouncedRef = customRef((track, trigger) => ({
		get() {
			track();
			return state.value;
		},
		set: debounce(
			(value: any) => {
				state.value = value;
				trigger();
			}, delay, immediate),
		})
	);
	return debouncedRef;
}

export function getItemFromStore(key: string, defaultValue?: string, store: Storage = localStorage) {
	try {
		return JSON.parse(store.getItem(key) as string) || defaultValue;
	} catch {
		return store.getItem(key) || defaultValue;
	}
};
  
export function setItemToStore(key: string, payload: string, store: Storage = localStorage) { store.setItem(key, payload) };

export function hasClass(el: Element, className: string) {
	!el && false;
	return el.classList.value.includes(className);
};

/**
 * Interface for AJAX Request Params
 * @interface RequestParams
 * @property {string} verb GET, POST, PUT, DELETE, etc...
 * @property {string} [url] Where the request is going
 * @property {any} [payload] Data to be sent with request
 * @property {any} [validationTarget]
 * @property {boolean} [refreshPage] Whether the page should be reloaded after the AJAX call is completed
 * @property {any} [success] Function to call on ajax success
 * @property {string|boolean} [contentType] Usually should be application/json
 * @property {boolean} [showToasts] Whether to show notifications or not
 * @property {boolean} [processData] Assumes data passed is an object and sends it as application/x-www-form-urlencoded
 * @property {boolean} [goBack] Whether the page should go back in history when the AJAX call is completed
 */
 export interface RequestParams {
    verb: string,
    url: string,
    payload?: any,
    validationTarget?: any,
    refreshPage?: boolean,
    success?: any,
    contentType?: string | boolean,
    showToasts?: boolean,
    processData?: boolean,
    goBack?: boolean,
    headers?: any
}

function checkContentType(str: string, types: string[]) {
	for (let type of types) if (str.includes(type)) return true;
}

/**
* @description Make an asynchronous network reqeust.  Default contentent type is applictionn/json
* @param {RequestParams} params All parameters in a single object
* @returns {Promise<T>} Javascript promise to be resolved when request finishes
*/
export function makeRequestAsync<T>(params: RequestParams): Promise<T> {
   let showToasts = (params.showToasts != undefined) ? params.showToasts : true;
   let contentType: string = "", responseAction: string;

   // Set the contentType
   if (typeof params.contentType == "string")
	   contentType = params.contentType;
   if (typeof params.contentType == "boolean")
	   contentType = "application/x-www-form-urlencoded;charset=UTF-8";
   else
	   contentType = "application/json;charset=UTF-8";

   let payloadContainsFormData = false;
   if (params.payload != undefined && params.payload.constructor != undefined && params.payload.constructor.name == "FormData") payloadContainsFormData = true;

   // Set the response parsing based on content type
   if (checkContentType(contentType, ["application/javascript", "text/html", "text/css", "text/plain", "application/x-www-form-urlencoded;charset=UTF-8"]))
	   responseAction = "text";
   else if (contentType.includes("application/json"))
	   responseAction = "json";
   // This is a little weird, but there are so many formats that are sent for blob that it seemed best to simply say, "everything else"
   else responseAction = "blob";

   // Deal with the payload as necessary
   let body = params.verb.toUpperCase() == "GET" ? undefined : params.payload;
   if (contentType == "application/x-www-form-urlencoded;charset=UTF-8" && params.payload) params.url += `?${queryString.stringify(params.payload)}`;
   else if (params.payload != null && typeof params.payload != "string")
	   body = JSON.stringify(params.payload);

   let headers: any;
   if (!payloadContainsFormData)
	   if (params.headers)            
		   headers = { "Content-Type": contentType, ...params.headers };
	   else headers = { "Content-Type": contentType };

   // Make the request
   return new Promise<T>((resolve, reject) => {
	   fetch(params.url, {
		   // Setting the default credentials is needed for Edge v42, not sure why....
		   method: params.verb.toUpperCase(), credentials: "same-origin",
		   headers,
		   body
	   })
		   .then(response => {
			   if (response.ok && response.status !== 204) {
				   if (response.redirected && response.url.includes("/Account/Login")) {
					//    toastr.error(
					// 	   "We're sorry, your login session has timed out, we're redirecting you to the login page. If this error persists, please contact technical support for help.",
					// 	   "Session Expired");
					   location.href = `/Account/login?returnUrl=${location.pathname}`;
					   return false;
				   }
				   const responseCopy: any = response.clone();
				   return responseCopy[responseAction]().catch((_: any) => response.text());
			   }
			   else if (response.ok) {
				   const responseCopy: any = response.clone();
				   return responseCopy[responseAction]().catch((_: any) => response.text());
			   }
			   // HTTP 409 Conflict will be caught by the page making the request
			   else if (response.status == 409)
				   reject(response);
			   else {
				   //if (showToasts) toastr.error("An error occurred", "Unsuccessful");
				   console.error(`Error in response: ${response.statusText}`);
				   console.log(response);
				   reject(response);
			   }
		   })
		   .then(data => resolve(data))
		   .catch(e => {
			   //if (showToasts) toastr.error("An error occurred", "Unsuccessful");
			   console.error(`Malformed Fetch operation: ${e.message}`);
			   reject(e);
		   });
   });
}

/**
     * @description RFC4122 Version 4 compliant UUID, read more here: https://gist.github.com/jed/982883
     * @returns String
     */
 export function UUID(): string {
	return (([1e7] as any) + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c: any) =>
		(c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
	)
}

/**
 * Return random numbers within the specified range
 * @param min {number} The minimum number from the range to return
 * @param max {number} The maximum number from the range to return
 * @param count {number} How many random numbers to return
 * @returns {Uint32Array} An array of the random numbers because that's how crypto.getRandomValues works
 */
function getRandomArray(min: number = 0, max: number = Number.MAX_SAFE_INTEGER, count: number = 1) {
	let randoms = crypto.getRandomValues(new Uint32Array(count));
	let rangeMax = max - min;
	for (let x = 0; x < randoms.length; x++)
		randoms[x] = (randoms[x] % rangeMax) + min;
	return randoms;
}

/**
 * Return a single random number
 * @param max {number} The largest number to return
 */
export function getRandom(max: number) { return getRandomArray(0, max)[0]; }