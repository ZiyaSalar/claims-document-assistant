import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from '../api';

const Ctx = createContext(null);
export const TYPES = [['admission_advice','Admission advice'],['discharge_summary','Discharge summary'],['hospital_bill','Hospital bill'],['signed_claim_form','Signed claim form']];
export const pretty = s => String(s ?? '—').replaceAll('_',' ');
export const shortId = s => String(s ?? '').slice(0,8).toUpperCase();
export const claimPath = id => `/claims/${encodeURIComponent(id)}`;
export function useApp() { return useContext(Ctx); }
export function AppProvider({ children }) {
  const [claims,setClaims] = useState([]);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const refresh = useCallback(async () => {
    setBusy(true);
    try { const result = await api('/api/claims/'); setClaims(Array.isArray(result) ? result : []); setError(''); return result; }
    catch(e) { setError(e.message); return []; }
    finally { setBusy(false); }
  },[]);
  useEffect(()=>{ refresh(); },[refresh]);
  return <Ctx.Provider value={{claims,refresh,busy,error,setError}}>{children}</Ctx.Provider>;
}
