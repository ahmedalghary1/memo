(() => {
  const arabicDigits = /[٠-٩۰-۹]/g;
  const digits = '٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹';
  const toLatin = value => String(value).replace(arabicDigits, digit => String(digits.indexOf(digit) % 10));

  const normalizePage = () => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) {
      const parent = walker.currentNode.parentElement;
      arabicDigits.lastIndex = 0;
      if (parent && !parent.closest('script,style,code,pre') && arabicDigits.test(walker.currentNode.nodeValue)) nodes.push(walker.currentNode);
    }
    nodes.forEach(node => { node.nodeValue = toLatin(node.nodeValue); });
    document.querySelectorAll('input,textarea').forEach(field => {
      if (field.value) field.value = toLatin(field.value);
      if (field.placeholder) field.placeholder = toLatin(field.placeholder);
    });
  };

  document.addEventListener('DOMContentLoaded', normalizePage);
  document.addEventListener('input', event => {
    const field = event.target;
    if (!(field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement)) return;
    const normalized = toLatin(field.value);
    if (normalized === field.value) return;
    const start = field.selectionStart;
    field.value = normalized;
    if (start !== null) field.setSelectionRange(start, start);
  });
  window.memoLatinDigits = toLatin;
})();
