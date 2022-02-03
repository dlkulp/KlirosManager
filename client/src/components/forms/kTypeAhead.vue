<template>
	<div class="typeahead">
		<label v-if="label" class="form-label" :for="id">{{label}}</label>
		<input type="text" class="form-control" :id="id" ref="typeahead" :placeholder="placeHolder" :disabled="disabled" />
	</div>
</template>

<script lang="ts">
import _autocomplete, {AutocompleteResult, AutocompleteItem} from "autocompleter";
import { defineComponent, ref, Ref, onMounted, onBeforeMount, PropType, toRefs, watch } from "vue";

export default defineComponent({
	props: {
		label: {type: String, default: ""},
		emptyMessage: {type: String, default: "No results found"},
		placeHolder: {type: String, default: "Search..."},
		displayKey: {type: String, default: ""},
		searchKeys: {type: Array as PropType<string[]>, default: []},
		items: {type: [String, Array] as PropType<string | AutocompleteItem[]>, default: ""},
		disabled: {type: Boolean, default: false},
		modelValue: {type: Object, default: null},
	},
	setup(props, {emit}) {
		const {modelValue, items, emptyMessage, displayKey, searchKeys} = toRefs(props);
		const curr = ref(modelValue.value);
		const typeahead = ref();
		const autocomplete: Ref<AutocompleteResult | undefined> = ref();
		let _items: AutocompleteItem[];
		const id = ref(`${Date.now()}${window.crypto.getRandomValues(new Uint32Array(1))[0]}`);

		onBeforeMount(async () => {
			if (typeof items.value === "string")
				_items = await fetch(items.value).then(i => i.json()); 
			else _items = items.value;
		});

		type Auto = AutocompleteItem;
		onMounted(() => {
			autocomplete.value = _autocomplete<Auto>({
				input: typeahead.value,
				emptyMsg: emptyMessage.value,
				minLength: 0,
				fetch(text: string, update: (items:AutocompleteItem[]) => void) {
					text = text.toLowerCase();
					let suggestions = _items.filter((n: any) => {
						let ret = n[searchKeys.value[0]].toString().toLowerCase().includes(text);
						for (let i = 1; i < searchKeys.value.length; i++)
							ret = ret || n[searchKeys.value[i]].toString().toLowerCase().includes(text);
						return ret;
					});
					update(suggestions);
				},
				onSelect(item: AutocompleteItem) {
					typeahead.value.value = (<any>item)[displayKey.value];
					curr.value = item;
					emit("update:modelValue", item);
				},
				render: function(item: AutocompleteItem): HTMLDivElement | undefined {
					const itemElement = document.createElement("div");
					itemElement.textContent = (<any>item)[displayKey.value];
					return itemElement;
				}
			});
		});

		// Get changes from original context
		watch(modelValue, newVal => {
			curr.value = newVal;
			typeahead.value.value = newVal[displayKey.value];
		});

		return {typeahead, autocomplete, id, curr};
	}
});
</script>

<style lang="scss">
.typeahead {
	--backgroundColor: #fff;
	--borderColor: #ced4da;
	--color: #212529;
	--box-shadow: rgb(55 90 127 / 25%);
}

@media (prefers-color-scheme: dark) {
	.typeahead {
		--backgroundColor: #222;
		--borderColor: #515151;
		--color: #b1b1b1;
		--box-shadow: rgb(13 110 253 / 25%);
	}
}
.typeahead input {
	padding: 0.3125rem 1rem 0.3125rem 2.25rem;
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Cpath fill='gray' d='M508.5 481.6l-129-129c-2.3-2.3-5.3-3.5-8.5-3.5h-10.3C395 312 416 262.5 416 208 416 93.1 322.9 0 208 0S0 93.1 0 208s93.1 208 208 208c54.5 0 104-21 141.1-55.2V371c0 3.2 1.3 6.2 3.5 8.5l129 129c4.7 4.7 12.3 4.7 17 0l9.9-9.9c4.7-4.7 4.7-12.3 0-17zM208 384c-97.3 0-176-78.7-176-176S110.7 32 208 32s176 78.7 176 176-78.7 176-176 176z' class=''%3E%3C/path%3E%3C/svg%3E");
	background-size: 1rem;
	background-position: left 0.75rem top 0.65rem;
	background-repeat: no-repeat;
	background-origin: border-box;
}

.typeahead input:focus {
	box-shadow: 0 0 0 0.25rem var(--box-shadow);
}
html.dark .typeahead input {
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Cpath fill='gainsboro' d='M508.5 481.6l-129-129c-2.3-2.3-5.3-3.5-8.5-3.5h-10.3C395 312 416 262.5 416 208 416 93.1 322.9 0 208 0S0 93.1 0 208s93.1 208 208 208c54.5 0 104-21 141.1-55.2V371c0 3.2 1.3 6.2 3.5 8.5l129 129c4.7 4.7 12.3 4.7 17 0l9.9-9.9c4.7-4.7 4.7-12.3 0-17zM208 384c-97.3 0-176-78.7-176-176S110.7 32 208 32s176 78.7 176 176-78.7 176-176 176z' class=''%3E%3C/path%3E%3C/svg%3E");
}
.autocomplete {
	font-size: 1rem;
	font-weight: 400;
	line-height: 1.5;
	color: var(--color);
	background-color: var(--backgroundColor);
	background-repeat: no-repeat;
	background-position: right 1rem center;
	background-size: 16px 12px;
	border: 1px solid var(--borderColor);
	border-radius: 0.33rem;
	box-shadow: var(--box-shadow);
	transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
	-webkit-appearance: none;
	appearance: none;
	z-index: 10000;
}

.autocomplete > div:hover:not(.group), .autocomplete > div.selected {
	background-color: var(--backgroundColor);
	color: var(--color);
	cursor: pointer;
}

.autocomplete > div {
	min-height: 1.2em;
	padding: 0.3125rem 3rem 0.3125rem 1rem;
}

.autocomplete * {
	font: inherit;
}
</style>