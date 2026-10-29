import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { api, ensureCsrf } from './api';
import type { Category, Equipment } from './api';
import { APP_NAME, BRAND_MARK } from './brand';

function money(value: string, currency = 'EUR') {
  return new Intl.NumberFormat('en-NL', { style: 'currency', currency, maximumFractionDigits: 2 }).format(Number(value));
}

const EQUIPMENT_IMAGES: Record<string, string> = {
  'air-compressor': '/images/equipment/air-compressor.jpg',
  'boom-lift': '/images/equipment/boom-lift.jpg',
  bulldozer: '/images/equipment/bulldozer.jpg',
  'concrete-mixer': '/images/equipment/concrete-mixer.jpg',
  'concrete-pump': '/images/equipment/concrete-pump.jpg',
  'concrete-vibrator': '/images/equipment/concrete-vibrator.jpg',
  'construction-heater': '/images/equipment/construction-heater.jpg',
  'dump-truck': '/images/equipment/dump-truck.jpg',
  'excavator-cat-320': '/images/equipment/excavator-cat-320.jpg',
  excavator: '/images/equipment/excavator-cat-320.jpg',
  forklift: '/images/equipment/forklift.jpg',
  generator: '/images/equipment/generator.jpg',
  'mini-excavator-kubota': '/images/equipment/mini-excavator-kubota.jpg',
  'mini-excavator': '/images/equipment/mini-excavator-kubota.jpg',
  'mobile-crane': '/images/equipment/mobile-crane.jpg',
  'road-roller': '/images/equipment/road-roller.jpg',
  'scaffolding': '/images/equipment/scaffolding.jpg',
  'scissor-lift': '/images/equipment/scissor-lift.jpg',
  'site-cabin': '/images/equipment/site-cabin.jpg',
  'site-fencing': '/images/equipment/site-fencing.jpg',
  'skid-steer-loader': '/images/equipment/skid-steer-loader.jpg',
  telehandler: '/images/equipment/telehandler.jpg',
  trencher: '/images/equipment/trencher.jpg',
  'wheel-loader-volvo': '/images/equipment/wheel-loader-volvo.jpg',
  'wheel-loader': '/images/equipment/wheel-loader-volvo.jpg',
};


function equipmentImage(item: Equipment): string {
  const categoryText = (item.categories ?? [])
    .map((category) => `${category.slug ?? ''} ${category.name ?? ''}`)
    .join(' ');

  const text = `${item.slug ?? ''} ${item.name ?? ''} ${categoryText}`
    .toLowerCase()
    .replace(/[_\s]+/g, '-');

  const aliases: Record<string, string> = {
    excavators: 'excavator',
    'mini-excavators': 'mini-excavator',
    'wheel-loaders': 'wheel-loader',
    'telehandlers': 'telehandler',
    'scissor-lifts': 'scissor-lift',
    'boom-lifts': 'boom-lift',
    forklifts: 'forklift',
    dumpers: 'dump-truck',
    rollers: 'road-roller',
    generators: 'generator',
    compressors: 'air-compressor',
    'concrete-mixers': 'concrete-mixer',
    pumps: 'concrete-pump',
    cranes: 'mobile-crane',
    trenchers: 'trencher',
    'skid-steers': 'skid-steer-loader',
    dozers: 'bulldozer',
    'site-cabins': 'site-cabin',
    fencing: 'site-fencing',
    heaters: 'construction-heater',
    scaffolding: 'scaffolding',
  };

  const keys = Object.keys(EQUIPMENT_IMAGES).sort(
    (a, b) => b.length - a.length,
  );

  const key = keys.find((candidate) => text.includes(candidate));

  if (key) return EQUIPMENT_IMAGES[key];

  const categoryKey = Object.keys(aliases).find(
    (candidate) => text.includes(candidate),
  );

  if (categoryKey) {
    return EQUIPMENT_IMAGES[aliases[categoryKey]];
  }

  return '/images/equipment/excavator-cat-320.jpg';
}


function Header() {
  return <header className="topbar"><Link className="brand" to="/"><span className="brand-mark">{BRAND_MARK}</span><span>{APP_NAME}</span></Link><nav><a href="#how-it-works">How it works</a><a href="#for-suppliers">For suppliers</a><Link to="/dashboard">My rentals</Link></nav><div className="top-actions"><Link className="login-link" to="/login">Log in</Link><Link className="button button-dark button-small" to="/register">Get started <span>↗</span></Link></div></header>;
}
function Footer() { return <footer className="footer"><Link className="brand" to="/"><span className="brand-mark">{BRAND_MARK}</span><span>{APP_NAME}</span></Link><span>Equipment rental, made straightforward.</span><span>© 2026 {APP_NAME}</span></footer>; }

function Catalog() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<Equipment[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [search, setSearch] = useState(searchParams.get('search') ?? '');
  const [city, setCity] = useState(searchParams.get('location__city') ?? '');
  const [category, setCategory] = useState(searchParams.get('category') ?? '');
  const [maxPrice, setMaxPrice] = useState(searchParams.get('max_price') ?? '');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [count, setCount] = useState(0);
  const query = useMemo(() => searchParams.toString(), [searchParams]);
  useEffect(() => {
    let active = true; setLoading(true); setError('');
    Promise.all([api<{ count: number; results: Equipment[] }>(`/api/catalog/equipment/${query ? `?${query}` : ''}`), api<Category[]>('/api/catalog/categories/')])
      .then(([catalog, cats]) => { if (active) { setItems(catalog.results ?? []); setCount(catalog.count ?? catalog.results?.length ?? 0); setCategories(cats); } })
      .catch((e: unknown) => { if (active) setError(e instanceof Error ? e.message : 'Unable to load equipment'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [query]);
  function submit(event: FormEvent) {
    event.preventDefault(); const params = new URLSearchParams();
    if (search.trim()) params.set('search', search.trim()); if (city.trim()) params.set('location__city', city.trim());
    if (category) params.set('category', category); if (maxPrice) params.set('max_price', maxPrice); setSearchParams(params);
  }
  return <><section className="hero"><div className="hero-grid" aria-hidden="true"></div><div className="hero-copy"><div className="eyebrow"><span className="pulse"></span> BUILT FOR THE WORK THAT BUILDS EVERYTHING</div><h1>Get the right gear.<br/><em>Keep work moving.</em></h1><p>Find dependable construction equipment from local rental companies. Clear rates, practical details, less chasing around.</p><div className="hero-stats"><div><strong>One place</strong><span>to discover equipment</span></div><div><strong>Clear pricing</strong><span>before you commit</span></div><div><strong>Built for teams</strong><span>and busy job sites</span></div></div></div><div className="hero-art" aria-hidden="true"><div className="art-orbit orbit-one"></div><div className="art-orbit orbit-two"></div><div className="art-card"><div className="art-label">SITE READY <span>↗</span></div><svg className="machine" viewBox="0 0 500 320" role="img"><ellipse cx="246" cy="275" rx="190" ry="20" fill="#b8b9aa"/><path d="M85 235 L115 205 L290 205 L335 238 L326 265 L100 265 Z" fill="#343b34"/><rect x="104" y="240" width="224" height="38" rx="18" fill="#232923"/><rect x="122" y="249" width="185" height="20" rx="10" fill="#687165"/><circle cx="158" cy="260" r="23" fill="#242a23" stroke="#949a86" strokeWidth="6"/><circle cx="282" cy="260" r="23" fill="#242a23" stroke="#949a86" strokeWidth="6"/><path d="M126 205 L158 135 L246 135 L286 205 Z" fill="#d4e533"/><path d="M166 144 L233 144 L260 193 L147 193 Z" fill="#64715f"/><path d="M179 143 L219 143 L241 183 L156 183 Z" fill="#a5b39b"/><path d="M244 140 L284 120 L337 68 L356 83 L306 153 L275 182" fill="none" stroke="#6c7a2c" strokeWidth="26" strokeLinecap="round"/><path d="M350 83 L395 74 L414 91 L380 107 Z" fill="#d4e533"/><path d="M395 78 L429 91 L405 117 L379 106 Z" fill="#4c5543"/><rect x="114" y="204" width="178" height="12" rx="4" fill="#a5b329"/><path d="M107 215 L85 242 L95 250 L125 221" fill="#3f473b"/></svg><div className="art-caption"><span>Built for real work</span><span className="caption-line"></span><span>01 / 03</span></div></div><div className="art-note"><span className="note-icon">↗</span><div><strong>More uptime.</strong><br/><span>Less admin.</span></div></div></div><div className="hero-bottom"><span>FIND EQUIPMENT THAT FITS THE JOB</span><span className="scroll-cue">SCROLL TO EXPLORE <b>↓</b></span></div></section>
  <section className="search-section" id="catalog"><div className="section-heading"><div><div className="eyebrow dark-eyebrow">THE EQUIPMENT DIRECTORY</div><h2>Find what your site needs.</h2></div><p>Compare equipment from suppliers<br/>in one straightforward search.</p></div><form className="search-panel" onSubmit={submit}><label className="search-field"><span>WHAT ARE YOU LOOKING FOR?</span><input value={search} onChange={e => setSearch(e.target.value)} placeholder="e.g. mini excavator, scissor lift"/><b>⌕</b></label><label className="search-field"><span>JOB SITE / AREA</span><input value={city} onChange={e => setCity(e.target.value)} placeholder="City or postcode"/><b>⌖</b></label><label className="search-field select-field"><span>EQUIPMENT TYPE</span><select value={category} onChange={e => setCategory(e.target.value)}><option value="">All categories</option>{categories.map(c => <option value={c.slug} key={c.id}>{c.name}</option>)}</select><b>⌄</b></label><label className="search-field price-field"><span>MAX. RATE (€)</span><input inputMode="decimal" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} placeholder="Any"/><b>€</b></label><button className="button button-lime search-button" type="submit">Search equipment <span>↗</span></button></form><div className="result-line"><span>{loading ? 'Searching the directory…' : `${count} ${count === 1 ? 'listing' : 'listings'} in the directory`}</span><span className="result-note">Rates shown by the supplier · Availability confirmed during booking</span></div>{error && <div className="notice error">{error}. Make sure the backend is running and the catalogue API is available.</div>}{loading ? <div className="loading-grid">{[1,2,3].map(n => <div className="skeleton" key={n}/>)}</div> : items.length ? <div className="equipment-grid">{items.map((item, i) => <EquipmentCard item={item} key={item.id} index={i}/>)}</div> : <div className="empty-state"><div className="empty-icon">⌕</div><h3>No equipment matches yet</h3><p>Try a broader search or remove a filter. Listings appear here when suppliers publish equipment in the backend.</p><button className="button button-outline" onClick={() => { setSearch(''); setCity(''); setCategory(''); setMaxPrice(''); setSearchParams({}); }}>Clear filters</button></div>}</section>
  <section className="steps-section" id="how-it-works"><div className="steps-intro"><div className="eyebrow">LESS ADMIN. MORE ON SITE.</div><h2>From search<br/>to site-ready.</h2><p>Built around the way equipment rental actually works — dates, rates and the details that matter.</p><Link to="/register" className="text-link">Get started <span>↗</span></Link></div><div className="steps-list"><div className="step"><span className="step-num">01</span><div><h3>Find your fit</h3><p>Search by type, area and budget. Review supplier information before you commit.</p></div><span className="step-symbol">⌕</span></div><div className="step"><span className="step-num">02</span><div><h3>Choose your dates</h3><p>Send a booking request for the dates you need. Server-side availability checks protect the schedule.</p></div><span className="step-symbol">▦</span></div><div className="step"><span className="step-num">03</span><div><h3>Keep the job moving</h3><p>Track booking status and, as features roll out, coordinate handover, return and maintenance.</p></div><span className="step-symbol">↗</span></div></div></section>
  <section className="supplier-banner" id="for-suppliers"><div><div className="eyebrow dark-eyebrow">FOR EQUIPMENT OWNERS</div><h2>Your fleet has work to do.</h2><p>Make your equipment easier to discover. Manage listings and rental activity from one workspace as the supplier features roll out.</p><Link className="button button-dark" to="/register">Join the supplier network <span>↗</span></Link></div><div className="supplier-art" aria-hidden="true"><div className="sun-disc"></div><div className="line-block block-a"></div><div className="line-block block-b"></div><div className="line-block block-c"></div><div className="supplier-word">ON SITE<span>.</span></div></div></section><Footer/></>;
}
function EquipmentCard({ item, index }: { item: Equipment; index: number }) {
  const kind = item.categories[0]?.name ?? 'Equipment';
  return <article className="equipment-card"><Link to={`/equipment/${item.slug}`} className={`equipment-visual visual-${index % 4}`} aria-label={`View ${item.name}`}><span className="visual-badge">{kind}</span><span className="visual-index">{String(index + 1).padStart(2, '0')}</span><img className="equipment-photo" src={equipmentImage(item)} alt={item.name} loading="lazy" onError={(event) => { event.currentTarget.onerror = null; event.currentTarget.src = '/images/equipment/excavator-cat-320.jpg';}} /><span className="visual-hint">VIEW DETAILS ↗</span></Link><div className="card-content"><div className="card-meta"><span>{item.company_name}</span><span className="availability-tag"><i/> Listed</span></div><h3><Link to={`/equipment/${item.slug}`}>{item.name}</Link></h3><p className="card-location">⌖ {item.location.city}, {item.location.country_code}</p><div className="card-bottom"><div><strong>{money(item.base_rate, item.currency)}</strong><span> / {item.billing_unit}</span>{Number(item.deposit_amount) > 0 && <small>Deposit {money(item.deposit_amount, item.currency)}</small>}</div><Link className="round-arrow" to={`/equipment/${item.slug}`} aria-label={`Details for ${item.name}`}>↗</Link></div></div></article>;
}
function EquipmentDetail() {
  const { slug = '' } = useParams(); const [item, setItem] = useState<Equipment | null>(null); const [error, setError] = useState(''); const [openBooking, setOpenBooking] = useState(false);
  useEffect(() => { api<Equipment>(`/api/catalog/equipment/${slug}/`).then(setItem).catch(e => setError(e.message)); }, [slug]);
  if (error) return <main className="page-shell"><div className="notice error">{error}</div><Link to="/">← Back to catalogue</Link></main>;
  if (!item) return <main className="page-shell"><p>Loading equipment details…</p></main>;
  return <main className="page-shell detail-page"><Link className="back-link" to="/">← Back to catalogue</Link><div className="detail-layout"><div className="detail-visual"><span className="visual-badge">{item.categories[0]?.name ?? 'Equipment'}</span><img className="detail-photo" src={equipmentImage(item)} alt={item.name} onError={(event) => { event.currentTarget.onerror = null; event.currentTarget.src = '/images/equipment/excavator-cat-320.jpg'; }} /></div><div className="detail-info"><div className="eyebrow dark-eyebrow">SUPPLIER LISTING</div><h1>{item.name}</h1><p className="detail-location">⌖ {item.location.city}, {item.location.country_code} · Listed by {item.company_name}</p><p className="detail-description">{item.description || 'Contact the supplier for equipment specifications, transport options and site requirements.'}</p><div className="detail-price"><div><strong>{money(item.base_rate, item.currency)}</strong><span> / {item.billing_unit}</span></div><small>{Number(item.deposit_amount) ? `Refundable deposit: ${money(item.deposit_amount, item.currency)}` : 'No deposit configured in this listing'}</small></div><div className="detail-facts"><span><b>Minimum duration</b>{item.minimum_rental_hours} hours</span><span><b>Currency</b>{item.currency}</span><span><b>Supplier</b>{item.company_name}</span></div><button className="button button-dark booking-cta" onClick={() => setOpenBooking(true)}>Request a booking <span>↗</span></button><p className="fine-print">Final price and availability are verified by the server. Payment processing is not enabled in this early version.</p></div></div>{openBooking && <BookingDialog item={item} close={() => setOpenBooking(false)}/>}</main>;
}
function BookingDialog({ item, close }: { item: Equipment; close: () => void }) {
  const [start, setStart] = useState(''); const [end, setEnd] = useState(''); const [busy, setBusy] = useState(false); const [message, setMessage] = useState(''); const [success, setSuccess] = useState(false);
  async function submit(e: FormEvent) { e.preventDefault(); setBusy(true); setMessage(''); try { await ensureCsrf(); const booking = await api<{ id: number; status: string; quoted_rental_amount: string; quoted_deposit_amount: string; currency: string }>('/api/bookings/', { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ equipment_id: item.id, starts_at: new Date(start).toISOString(), ends_at: new Date(end).toISOString() }) }); setSuccess(true); setMessage(`Request #${booking.id} created. Rental quote ${money(booking.quoted_rental_amount, booking.currency)}; deposit ${money(booking.quoted_deposit_amount, booking.currency)}. Status: ${booking.status}. Payment is disabled.`); } catch (err) { setMessage(err instanceof Error ? err.message : 'Booking request failed'); } finally { setBusy(false); } }
  return <div className="modal-backdrop" role="presentation" onMouseDown={e => { if (e.target === e.currentTarget) close(); }}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="booking-title"><button className="modal-close" onClick={close} aria-label="Close">×</button><div className="eyebrow dark-eyebrow">BOOKING REQUEST</div><h2 id="booking-title">Choose your dates</h2><p>{item.name} · {item.company_name}</p><form onSubmit={submit} className="booking-form"><label>Start date & time<input required type="datetime-local" value={start} onChange={e => setStart(e.target.value)}/></label><label>End date & time<input required type="datetime-local" min={start || undefined} value={end} onChange={e => setEnd(e.target.value)}/></label><button className="button button-dark" disabled={busy || success}>{busy ? 'Checking availability…' : success ? 'Request created' : 'Request booking'} <span>↗</span></button></form>{message && <div className={`notice ${success ? 'success' : 'error'}`} role="status">{message}</div>}<p className="fine-print">Requires sign-in. The server validates dates, current tariff and availability. No card details are collected by this app.</p></section></div>;
}
function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const navigate = useNavigate(); const [email, setEmail] = useState(''); const [displayName, setDisplayName] = useState(''); const [password, setPassword] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const register = mode === 'register';
  async function submit(e: FormEvent) { e.preventDefault(); setBusy(true); setError(''); try { await ensureCsrf(); if (register) { await api('/api/auth/register/', { method: 'POST', body: JSON.stringify({ email, display_name: displayName, password }) }); navigate('/login'); return; } else { await api('/api/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) }); } navigate('/dashboard'); } catch (err) { setError(err instanceof Error ? err.message : 'Authentication failed'); } finally { setBusy(false); } }
  return <main className="auth-shell"><div className="auth-card"><Link className="back-link" to="/">← Back to home</Link><div className="brand auth-brand"><span className="brand-mark">{BRAND_MARK}</span><span>{APP_NAME}</span></div><div className="eyebrow dark-eyebrow">{register ? 'CREATE YOUR ACCOUNT' : 'WELCOME BACK'}</div><h1>{register ? 'Build a better workday.' : 'Good to see you again.'}</h1><p>{register ? 'Set up your account to request rentals and manage your equipment activity.' : 'Sign in to manage your rental requests.'}</p><form onSubmit={submit} className="booking-form">{register && <label>Your name<input required autoComplete="name" value={displayName} onChange={e => setDisplayName(e.target.value)}/></label>}<label>Work email<input required type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)}/></label><label>Password<input required type="password" minLength={12} autoComplete={register ? 'new-password' : 'current-password'} value={password} onChange={e => setPassword(e.target.value)}/></label><button className="button button-dark" disabled={busy}>{busy ? 'Please wait…' : register ? 'Create account' : 'Log in'} <span>↗</span></button></form>{error && <div className="notice error" role="alert">{error}</div>}<p className="auth-switch">{register ? 'Already have an account?' : `New to ${APP_NAME}?`} <Link to={register ? '/login' : '/register'}>{register ? 'Log in' : 'Create an account'}</Link></p>{register && <p className="fine-print">Email verification and password-reset email workflows must be configured before production use.</p>}</div></main>;
}
function Dashboard() { const [profile, setProfile] = useState<{ email: string; display_name: string } | null>(null); const [bookings, setBookings] = useState<Array<{id:number;equipment_name:string;starts_at:string;ends_at:string;status:string;quoted_rental_amount:string;currency:string}>>([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true); const navigate = useNavigate(); useEffect(() => { Promise.all([api<{email:string;display_name:string}>('/api/auth/me/'), api<Array<{id:number;equipment_name:string;starts_at:string;ends_at:string;status:string;quoted_rental_amount:string;currency:string}>>('/api/bookings/')]).then(([user,items]) => {setProfile(user);setBookings(items)}).catch(e => setError(e.message)).finally(() => setLoading(false)); }, []); async function signout(){try{await ensureCsrf();await api('/api/auth/logout/',{method:'POST'});navigate('/')}catch(e){setError(e instanceof Error?e.message:'Sign-out failed')}} return <main className="page-shell dashboard-page"><div className="eyebrow dark-eyebrow">YOUR WORKSPACE</div><h1>My rentals</h1>{loading ? <p>Loading your account…</p> : error ? <div className="notice error">{error} <Link to="/login">Sign in</Link></div> : <><div className="dashboard-heading"><div><p>{profile?.display_name || profile?.email}</p><span>{profile?.email}</span></div><button className="button button-outline" onClick={signout}>Sign out</button></div><h2>Booking requests</h2>{bookings.length ? <div className="booking-list">{bookings.map(b => <article key={b.id}><div><strong>#{b.id} · {b.equipment_name}</strong><span>{new Date(b.starts_at).toLocaleString()} – {new Date(b.ends_at).toLocaleString()}</span></div><div><span className="status-pill">{b.status.replaceAll('_',' ')}</span><strong>{money(b.quoted_rental_amount,b.currency)}</strong></div></article>)}</div> : <div className="empty-state compact"><h3>No rental requests yet</h3><p>Your submitted bookings will appear here.</p><Link className="button button-dark" to="/">Browse equipment <span>↗</span></Link></div>}</>}</main>; }

export default function App() { return <><Header/><Routes><Route path="/" element={<Catalog/>}/><Route path="/equipment/:slug" element={<EquipmentDetail/>}/><Route path="/login" element={<AuthPage mode="login"/>}/><Route path="/register" element={<AuthPage mode="register"/>}/><Route path="/dashboard" element={<Dashboard/>}/><Route path="*" element={<main className="page-shell"><h1>Page not found</h1><Link to="/">Back to catalogue</Link></main>}/></Routes></>; }
