import { ref, customRef } from "vue";

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