export const themes = {
  1: { name: '极地白', background: '#ffffff', surface: '#f5f5f5', primary: '#2563eb', text: '#0f172a', accent: '#0ea5e9', border: '#d4d4d8' },
  2: { name: '2', background: '#f2f2f2', surface: '#e8e8e8', primary: '#3159e8', text: '#111827', accent: '#0ea5e9', border: '#d4d4d8' },
  3: { name: '3', background: '#e5e5e5', surface: '#dbdbdb', primary: '#3d50e3', text: '#1f2937', accent: '#06b6d4', border: '#cbd5e1' },
  4: { name: '暖米色', background: '#d8d8d8', surface: '#cec6bf', primary: '#7c3aed', text: '#1f2937', accent: '#f59e0b', border: '#b9b2aa' },
  5: { name: '5', background: '#cbcbcb', surface: '#c1c1c1', primary: '#8b5cf6', text: '#1f2937', accent: '#f97316', border: '#a8a8a8' },
  6: { name: '6', background: '#bebebe', surface: '#b4b4b4', primary: '#9333ea', text: '#111827', accent: '#f43f5e', border: '#9ca3af' },
  7: { name: '7', background: '#b1b1b1', surface: '#a7a7a7', primary: '#7c3aed', text: '#111827', accent: '#ef4444', border: '#8f8f8f' },
  8: { name: '8', background: '#a4a4a4', surface: '#9a9a9a', primary: '#6d28d9', text: '#f8fafc', accent: '#ec4899', border: '#7f7f7f' },
  9: { name: '9', background: '#979797', surface: '#8d8d8d', primary: '#5b21b6', text: '#f8fafc', accent: '#d946ef', border: '#737373' },
  10: { name: '暮灰', background: '#8a8a8a', surface: '#808080', primary: '#4338ca', text: '#f8fafc', accent: '#22d3ee', border: '#666666' },
  11: { name: '11', background: '#7d7d7d', surface: '#737373', primary: '#1d4ed8', text: '#f8fafc', accent: '#14b8a6', border: '#595959' },
  12: { name: '12', background: '#707070', surface: '#666666', primary: '#0369a1', text: '#f8fafc', accent: '#10b981', border: '#4d4d4d' },
  13: { name: '13', background: '#636363', surface: '#595959', primary: '#047857', text: '#f8fafc', accent: '#84cc16', border: '#404040' },
  14: { name: '14', background: '#565656', surface: '#4c4c4c', primary: '#166534', text: '#f8fafc', accent: '#facc15', border: '#333333' },
  15: { name: '深蓝夜', background: '#494949', surface: '#2a3140', primary: '#1d4ed8', text: '#e2e8f0', accent: '#38bdf8', border: '#1f2937' },
  16: { name: '16', background: '#3c3c3c', surface: '#343434', primary: '#0f766e', text: '#e2e8f0', accent: '#2dd4bf', border: '#262626' },
  17: { name: '17', background: '#2f2f2f', surface: '#272727', primary: '#7c2d12', text: '#e2e8f0', accent: '#fb923c', border: '#1f1f1f' },
  18: { name: '18', background: '#222222', surface: '#1f1f1f', primary: '#7f1d1d', text: '#e2e8f0', accent: '#f87171', border: '#181818' },
  19: { name: '19', background: '#151515', surface: '#131313', primary: '#581c87', text: '#e2e8f0', accent: '#c084fc', border: '#0f0f0f' },
  20: { name: '纯黑', background: '#000000', surface: '#0a0a0a', primary: '#312e81', text: '#f8fafc', accent: '#818cf8', border: '#1f2937' }
};

export const themeEntries = Object.entries(themes).map(([id, theme]) => ({ id: Number(id), ...theme }));

export function getTheme(themeId) {
  return themes[themeId] || themes[10];
}
