/**
 * C-Drive DormantSpace Scope - Frontend Controller
 * Complete presentation slides engine, interactive explorer, canvas charts,
 * and Windows File Explorer bridge.
 */

// If opened via file:/// protocol, redirect API calls to the local server
const API_BASE = (window.location.protocol === 'file:' || window.location.origin === 'null' || !window.location.origin)
  ? 'http://127.0.0.1:8765'
  : '';

// Application State
const state = {
  view: 'presentation', // 'presentation' | 'explorer'
  currentSlide: 1,
  totalSlides: 5,
  isAutoplay: false,
  autoplayInterval: null,
  isScanning: false,
  pollInterval: null,
  
  driveInfo: {},
  presets: [],
  results: [],
  analytics: {},
  
  // Table filters & sorting
  searchTerm: '',
  selectedCategory: 'ALL',
  sortCol: 'size_bytes',
  sortDir: 'desc',
  
  selectedFile: null,
  skipDeleteConfirmation: false,
  pendingDeleteFile: null,
  pendingDeleteRow: null,
  deniedFile: null
};

// DOM Elements Cache
const elements = {
  // Views & Header
  viewBtnPresentation: document.getElementById('viewBtnPresentation'),
  viewBtnExplorer: document.getElementById('viewBtnExplorer'),
  presentationView: document.getElementById('presentationView'),
  explorerView: document.getElementById('explorerView'),
  themeToggleBtn: document.getElementById('themeToggleBtn'),
  themeIcon: document.getElementById('themeIcon'),
  exportCsvBtn: document.getElementById('exportCsvBtn'),
  exportPresentationBtn: document.getElementById('exportPresentationBtn'),

  // Controls
  targetPathInput: document.getElementById('targetPathInput'),
  presetBadge: document.getElementById('presetBadge'),
  presetMenuBtn: document.getElementById('presetMenuBtn'),
  presetMenu: document.getElementById('presetMenu'),
  minSizeSelect: document.getElementById('minSizeSelect'),
  minDaysSelect: document.getElementById('minDaysSelect'),
  dateBasisSelect: document.getElementById('dateBasisSelect'),
  startScanBtn: document.getElementById('startScanBtn'),
  stopScanBtn: document.getElementById('stopScanBtn'),

  // Progress
  scanProgressCard: document.getElementById('scanProgressCard'),
  progressStatusText: document.getElementById('progressStatusText'),
  progressCurrentDir: document.getElementById('progressCurrentDir'),
  progressFilesCount: document.getElementById('progressFilesCount'),
  progressSpeed: document.getElementById('progressSpeed'),
  progressDormantCount: document.getElementById('progressDormantCount'),
  progressDormantBytes: document.getElementById('progressDormantBytes'),

  // Presentation Navigation
  prevSlideBtn: document.getElementById('prevSlideBtn'),
  nextSlideBtn: document.getElementById('nextSlideBtn'),
  slideIndicators: document.getElementById('slideIndicators'),
  slideNumberDisplay: document.getElementById('slideNumberDisplay'),
  autoplayBtn: document.getElementById('autoplayBtn'),
  autoplayIcon: document.getElementById('autoplayIcon'),
  fullscreenBtn: document.getElementById('fullscreenBtn'),

  // Slide 1 Elements
  driveSummaryText: document.getElementById('driveSummaryText'),
  barUsed: document.getElementById('barUsed'),
  barDormant: document.getElementById('barDormant'),
  barFree: document.getElementById('barFree'),
  metricActiveUsed: document.getElementById('metricActiveUsed'),
  metricDormantReclaim: document.getElementById('metricDormantReclaim'),
  metricFree: document.getElementById('metricFree'),
  cardTotalCapacity: document.getElementById('cardTotalCapacity'),
  cardCapacitySub: document.getElementById('cardCapacitySub'),
  cardDormantWaste: document.getElementById('cardDormantWaste'),
  cardDormantSub: document.getElementById('cardDormantSub'),
  cardSafeReclaim: document.getElementById('cardSafeReclaim'),
  cardDormantCount: document.getElementById('cardDormantCount'),
  cardDormantCountSub: document.getElementById('cardDormantCountSub'),
  healthGradeBadge: document.getElementById('healthGradeBadge'),

  // Slide 2 Elements
  ageDistributionChart: document.getElementById('ageDistributionChart'),
  ageCardsContainer: document.getElementById('ageCardsContainer'),

  // Slide 3 Elements
  topCulpritsGrid: document.getElementById('topCulpritsGrid'),

  // Slide 4 Elements
  folderHotspotsList: document.getElementById('folderHotspotsList'),
  categoryDistributionChart: document.getElementById('categoryDistributionChart'),
  categoryChipsWrap: document.getElementById('categoryChipsWrap'),

  // Slide 5 Elements
  roadSafeGB: document.getElementById('roadSafeGB'),
  roadReviewGB: document.getElementById('roadReviewGB'),
  btnFilterSafeWins: document.getElementById('btnFilterSafeWins'),
  btnFilterReviewMedia: document.getElementById('btnFilterReviewMedia'),
  btnOpenWinSettings: document.getElementById('btnOpenWinSettings'),

  // Explorer Table
  fileSearchInput: document.getElementById('fileSearchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  categoryFiltersRow: document.getElementById('categoryFiltersRow'),
  showingCount: document.getElementById('showingCount'),
  totalCount: document.getElementById('totalCount'),
  showingSize: document.getElementById('showingSize'),
  dormantTable: document.getElementById('dormantTable'),
  dormantTableBody: document.getElementById('dormantTableBody'),
  noResultsMsg: document.getElementById('noResultsMsg'),

  // Modal
  fileModal: document.getElementById('fileModal'),
  modalFileName: document.getElementById('modalFileName'),
  modalBody: document.getElementById('modalBody'),
  modalCloseBtn: document.getElementById('modalCloseBtn'),
  modalCloseFooterBtn: document.getElementById('modalCloseFooterBtn'),
  modalOpenExplorerBtn: document.getElementById('modalOpenExplorerBtn'),
  modalOpenFolderBtn: document.getElementById('modalOpenFolderBtn'),
  modalCopyPathBtn: document.getElementById('modalCopyPathBtn'),
  modalDeleteBtn: document.getElementById('modalDeleteBtn'),

  // Delete Modal
  deleteModal: document.getElementById('deleteModal'),
  deleteModalCloseBtn: document.getElementById('deleteModalCloseBtn'),
  deleteModalFileName: document.getElementById('deleteModalFileName'),
  deleteModalFilePath: document.getElementById('deleteModalFilePath'),
  deleteModalFileSize: document.getElementById('deleteModalFileSize'),
  deleteModalFileDays: document.getElementById('deleteModalFileDays'),
  skipDeleteConfirmCheck: document.getElementById('skipDeleteConfirmCheck'),
  confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
  cancelDeleteBtn: document.getElementById('cancelDeleteBtn'),

  // Access Denied Guidance Modal
  accessDeniedModal: document.getElementById('accessDeniedModal'),
  accessDeniedCloseBtn: document.getElementById('accessDeniedCloseBtn'),
  deniedModalFileName: document.getElementById('deniedModalFileName'),
  deniedModalFilePath: document.getElementById('deniedModalFilePath'),
  deniedOpenExplorerBtn: document.getElementById('deniedOpenExplorerBtn'),
  deniedOpenFolderBtn: document.getElementById('deniedOpenFolderBtn'),
  deniedCopyPathBtn: document.getElementById('deniedCopyPathBtn'),
  deniedCloseFooterBtn: document.getElementById('deniedCloseFooterBtn'),

  // Toast
  toastNotification: document.getElementById('toastNotification'),
  toastIcon: document.getElementById('toastIcon'),
  toastMessage: document.getElementById('toastMessage')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  initTheme();
  initSlideIndicators();
  loadInitialData();
});

// Event Listeners
function initEventListeners() {
  // View Toggle
  elements.viewBtnPresentation.addEventListener('click', () => switchView('presentation'));
  elements.viewBtnExplorer.addEventListener('click', () => switchView('explorer'));

  // Theme Toggle
  elements.themeToggleBtn.addEventListener('click', toggleTheme);

  // Scan Controls
  elements.startScanBtn.addEventListener('click', startScan);
  elements.stopScanBtn.addEventListener('click', stopScan);
  elements.presetMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    elements.presetMenu.classList.toggle('hidden');
  });
  document.addEventListener('click', () => elements.presetMenu.classList.add('hidden'));

  // Quick Preset Pills
  document.querySelectorAll('.quick-presets-pills .pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.quick-presets-pills .pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const target = btn.dataset.path;
      applyPresetTarget(target, btn.textContent.trim());
    });
  });

  // Presentation Navigation
  elements.prevSlideBtn.addEventListener('click', () => changeSlide(-1));
  elements.nextSlideBtn.addEventListener('click', () => changeSlide(1));
  elements.autoplayBtn.addEventListener('click', toggleAutoplay);
  elements.fullscreenBtn.addEventListener('click', toggleFullscreen);

  // Keyboard navigation for presentation
  document.addEventListener('keydown', (e) => {
    if (state.view === 'presentation') {
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === 'Space') {
        changeSlide(1);
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        changeSlide(-1);
      }
    }
  });

  // Slide 5 Quick Navigation Actions
  elements.btnFilterSafeWins.addEventListener('click', () => {
    switchView('explorer');
    setCategoryFilter('SAFE_ONLY');
  });

  elements.btnFilterReviewMedia.addEventListener('click', () => {
    switchView('explorer');
    setCategoryFilter('Media & Video');
  });

  elements.btnOpenWinSettings.addEventListener('click', () => {
    showToast('Tip: In Windows 11, open Settings > System > Storage to manage Storage Sense and Hibernation.', '💡', 6000);
  });

  // Explorer Table Search & Filter
  elements.fileSearchInput.addEventListener('input', (e) => {
    state.searchTerm = e.target.value.toLowerCase().trim();
    elements.clearSearchBtn.classList.toggle('hidden', state.searchTerm.length === 0);
    renderTable();
  });

  elements.clearSearchBtn.addEventListener('click', () => {
    elements.fileSearchInput.value = '';
    state.searchTerm = '';
    elements.clearSearchBtn.classList.add('hidden');
    renderTable();
  });

  // Category filter pills
  elements.categoryFiltersRow.addEventListener('click', (e) => {
    const pill = e.target.closest('.cat-pill');
    if (!pill) return;
    setCategoryFilter(pill.dataset.cat);
  });

  // Table header sorting
  elements.dormantTable.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.sort;
      if (state.sortCol === col) {
        state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        state.sortCol = col;
        state.sortDir = 'desc';
      }
      updateSortingHeaders();
      renderTable();
    });
  });

  // Modal actions
  elements.modalCloseBtn.addEventListener('click', closeModal);
  elements.modalCloseFooterBtn.addEventListener('click', closeModal);
  elements.fileModal.addEventListener('click', (e) => {
    if (e.target === elements.fileModal) closeModal();
  });

  elements.modalOpenExplorerBtn.addEventListener('click', () => {
    if (state.selectedFile) openInExplorer(state.selectedFile.path, 'select');
  });

  elements.modalOpenFolderBtn.addEventListener('click', () => {
    if (state.selectedFile) openInExplorer(state.selectedFile.path, 'folder');
  });

  elements.modalCopyPathBtn.addEventListener('click', () => {
    if (state.selectedFile) copyToClipboard(state.selectedFile.path);
  });

  elements.modalDeleteBtn.addEventListener('click', () => {
    if (state.selectedFile) promptDelete(state.selectedFile);
  });

  // Delete modal actions
  elements.deleteModalCloseBtn.addEventListener('click', closeDeleteModal);
  elements.cancelDeleteBtn.addEventListener('click', closeDeleteModal);
  elements.deleteModal.addEventListener('click', (e) => {
    if (e.target === elements.deleteModal) closeDeleteModal();
  });
  elements.confirmDeleteBtn.addEventListener('click', () => {
    if (elements.skipDeleteConfirmCheck.checked) {
      state.skipDeleteConfirmation = true;
    }
    if (state.pendingDeleteFile) {
      const file = state.pendingDeleteFile;
      const row = state.pendingDeleteRow;
      closeDeleteModal();
      executeDelete(file, row);
    }
  });

  // Access Denied Guidance modal actions
  elements.accessDeniedCloseBtn.addEventListener('click', closeAccessDeniedModal);
  elements.deniedCloseFooterBtn.addEventListener('click', closeAccessDeniedModal);
  elements.accessDeniedModal.addEventListener('click', (e) => {
    if (e.target === elements.accessDeniedModal) closeAccessDeniedModal();
  });
  elements.deniedOpenExplorerBtn.addEventListener('click', () => {
    if (state.deniedFile) {
      openInExplorer(state.deniedFile.path, 'select');
      closeAccessDeniedModal();
    }
  });
  elements.deniedOpenFolderBtn.addEventListener('click', () => {
    if (state.deniedFile) {
      openInExplorer(state.deniedFile.path, 'folder');
      closeAccessDeniedModal();
    }
  });
  elements.deniedCopyPathBtn.addEventListener('click', () => {
    if (state.deniedFile) {
      copyToClipboard(state.deniedFile.path);
    }
  });

  // Export buttons
  elements.exportCsvBtn.addEventListener('click', () => {
    window.location.href = `${API_BASE}/api/export/csv`;
    showToast('Exporting CSV report...', '📥');
  });

  elements.exportPresentationBtn.addEventListener('click', () => {
    window.location.href = `${API_BASE}/api/export/presentation`;
    showToast('Generating standalone Executive Presentation...', '📑');
  });
}

// Initial Data Fetch
async function loadInitialData() {
  try {
    // 1. Fetch Drive Info
    const driveRes = await fetch(`${API_BASE}/api/drive-info`);
    if (driveRes.ok) {
      state.driveInfo = await driveRes.json();
      updateDriveMeters();
    }

    // 2. Fetch Presets
    const presetRes = await fetch(`${API_BASE}/api/presets`);
    if (presetRes.ok) {
      const data = await presetRes.json();
      state.presets = data.presets || [];
      populatePresetsMenu();
    }

    // 3. Check for existing results
    const resultsRes = await fetch(`${API_BASE}/api/scan/results`);
    if (resultsRes.ok) {
      const data = await resultsRes.json();
      if (data.results && data.results.length > 0) {
        state.results = data.results;
        state.analytics = data.analytics;
        renderAllViews();
      } else {
        // Automatically start initial user profile scan for great out-of-the-box experience
        startScan();
      }
    }
  } catch (err) {
    console.error('Error loading initial data:', err);
  }
}

// Presets Menu Population
function populatePresetsMenu() {
  elements.presetMenu.innerHTML = '';
  state.presets.forEach(p => {
    const item = document.createElement('div');
    item.className = 'dropdown-item';
    item.innerHTML = `
      <div style="font-weight:600;">${p.name}</div>
      <div class="dropdown-item-desc">${p.path} &bull; ${p.description}</div>
    `;
    item.addEventListener('click', () => {
      elements.targetPathInput.value = p.path;
      elements.presetBadge.textContent = p.name.split('(')[0].trim();
      elements.presetMenu.classList.add('hidden');
    });
    elements.presetMenu.appendChild(item);
  });
}

function applyPresetTarget(key, label) {
  let path = 'C:\\Users';
  if (key === 'USER_PROFILE') {
    const userPreset = state.presets.find(p => p.id === 'user_profile');
    path = userPreset ? userPreset.path : 'C:\\Users';
  } else if (key === 'DOWNLOADS') {
    const dlPreset = state.presets.find(p => p.id === 'user_downloads');
    path = dlPreset ? dlPreset.path : 'C:\\Users';
  } else if (key === 'DEV_CACHES') {
    const cachePreset = state.presets.find(p => p.id === 'user_caches');
    path = cachePreset ? cachePreset.path : 'C:\\Users';
  } else if (key === 'C:\\') {
    path = 'C:\\';
  }
  elements.targetPathInput.value = path;
  elements.presetBadge.textContent = label;
}

// Scan Lifecycle
async function startScan() {
  const targetPath = elements.targetPathInput.value.trim() || 'C:\\';
  const minSizeMb = parseFloat(elements.minSizeSelect.value);
  const minDays = parseInt(elements.minDaysSelect.value);
  const dateBasis = elements.dateBasisSelect.value;

  try {
    elements.startScanBtn.classList.add('hidden');
    elements.stopScanBtn.classList.remove('hidden');
    elements.scanProgressCard.classList.remove('hidden');
    state.isScanning = true;

    const res = await fetch(`${API_BASE}/api/scan/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_path: targetPath,
        min_size_mb: minSizeMb,
        min_dormant_days: minDays,
        date_basis: dateBasis,
        skip_system_dirs: true
      })
    });

    if (res.ok) {
      showToast(`Scanning started for ${targetPath}`, '🔍');
      // Begin polling status
      if (state.pollInterval) clearInterval(state.pollInterval);
      state.pollInterval = setInterval(pollScanStatus, 600);
    }
  } catch (err) {
    showToast('Failed to start scan: ' + err.message, '⚠️');
    resetScanButtons();
  }
}

async function stopScan() {
  try {
    await fetch(`${API_BASE}/api/scan/stop`, { method: 'POST' });
    showToast('Stopping scanner...', '⏹');
  } catch (err) {
    console.error(err);
  }
}

async function pollScanStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/scan/status`);
    if (!res.ok) return;
    const st = await res.json();

    elements.progressStatusText.textContent = st.status_message || 'Scanning...';
    elements.progressCurrentDir.textContent = st.current_dir || '';
    elements.progressFilesCount.textContent = st.files_scanned.toLocaleString();
    elements.progressSpeed.textContent = (st.scan_rate_fps || 0).toLocaleString();
    elements.progressDormantCount.textContent = st.dormant_found.toLocaleString();
    elements.progressDormantBytes.textContent = formatBytes(st.dormant_bytes);

    if (!st.is_scanning) {
      // Scan finished!
      clearInterval(state.pollInterval);
      state.pollInterval = null;
      state.isScanning = false;
      resetScanButtons();
      
      // Fetch full results
      await fetchAndDisplayResults();
      showToast(`Scan complete! Found ${st.dormant_found} dormant files.`, '✅');
    }
  } catch (err) {
    console.error('Poll error:', err);
  }
}

function resetScanButtons() {
  elements.startScanBtn.classList.remove('hidden');
  elements.stopScanBtn.classList.add('hidden');
  elements.scanProgressCard.classList.add('hidden');
}

async function fetchAndDisplayResults() {
  try {
    const res = await fetch(`${API_BASE}/api/scan/results`);
    if (res.ok) {
      const data = await res.json();
      state.results = data.results || [];
      state.analytics = data.analytics || {};
      state.driveInfo = data.drive_info || state.driveInfo;
      renderAllViews();
    }
  } catch (err) {
    console.error('Error fetching results:', err);
  }
}

// Render All Views
function renderAllViews() {
  updateDriveMeters();
  renderSlide1Overview();
  renderSlide2AgeSpectrum();
  renderSlide3TopCulprits();
  renderSlide4HotspotsAndCategories();
  renderSlide5Roadmap();
  renderTable();
}

// Slide 1: Executive Overview
function updateDriveMeters() {
  const d = state.driveInfo;
  if (!d.total_gb) return;

  const dormantGb = state.analytics.total_dormant_gb || 0;
  const dormantPct = Math.min(d.used_pct, Math.round((dormantGb / d.total_gb) * 100));
  const activeUsedPct = Math.max(0, d.used_pct - dormantPct);

  elements.driveSummaryText.textContent = `${d.used_gb} GB Used of ${d.total_gb} GB (${d.free_gb} GB Free)`;
  elements.barUsed.style.width = `${activeUsedPct}%`;
  elements.barDormant.style.width = `${dormantPct}%`;
  elements.barFree.style.width = `${d.free_pct}%`;

  elements.metricActiveUsed.textContent = `${(d.used_gb - dormantGb).toFixed(1)} GB (${activeUsedPct}%)`;
  elements.metricDormantReclaim.textContent = `${dormantGb} GB (${dormantPct}%)`;
  elements.metricFree.textContent = `${d.free_gb} GB (${d.free_pct}%)`;

  // Compute Health Grade
  let grade = 'A';
  let badgeClass = 'badge-safe';
  if (d.used_pct > 90) {
    grade = 'D';
    badgeClass = 'badge-system';
  } else if (d.used_pct > 80) {
    grade = 'C+';
    badgeClass = 'badge-caution';
  } else if (d.used_pct > 65) {
    grade = 'B+';
    badgeClass = 'badge-review';
  }

  const gradeLetter = elements.healthGradeBadge.querySelector('.grade-letter');
  if (gradeLetter) gradeLetter.textContent = grade;
}

function renderSlide1Overview() {
  const a = state.analytics;
  const d = state.driveInfo;

  elements.cardTotalCapacity.textContent = d.total_gb ? `${d.total_gb} GB` : '-';
  elements.cardCapacitySub.textContent = `${d.used_pct || 0}% Occupied \u2022 ${d.free_gb || 0} GB Free`;

  elements.cardDormantWaste.textContent = a.total_dormant_formatted || '0 B';
  elements.cardDormantSub.textContent = `${a.reclaim_of_used_pct || 0}% of used space`;

  elements.cardSafeReclaim.textContent = a.safe_formatted || '0 B';
  elements.cardDormantCount.textContent = (a.total_dormant_files || state.results.length).toLocaleString();
  elements.cardDormantCountSub.textContent = `Inactive space-occupying items`;
}

// Slide 2: Age Spectrum
function renderSlide2AgeSpectrum() {
  const a = state.analytics;
  const ageData = a.age_distribution || [];
  elements.ageCardsContainer.innerHTML = '';

  ageData.forEach(tier => {
    const card = document.createElement('div');
    card.className = 'spectrum-card';
    card.style.borderLeftColor = tier.color;
    card.innerHTML = `
      <div>
        <div class="spectrum-title">${tier.label} Inactive</div>
        <div class="spectrum-sub">${tier.count} files untouched \u2022 Avg ${(tier.gb || 0)} GB</div>
      </div>
      <div class="spectrum-size" style="color: ${tier.color};">${tier.formatted}</div>
    `;
    elements.ageCardsContainer.appendChild(card);
  });

  drawHorizontalBarChart(elements.ageDistributionChart, ageData);
}

// Slide 3: Top Culprits Leaderboard
function renderSlide3TopCulprits() {
  const wasters = state.analytics.top_space_wasters || state.results.slice(0, 6);
  elements.topCulpritsGrid.innerHTML = '';

  if (!wasters || wasters.length === 0) {
    elements.topCulpritsGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-muted);">
        No large dormant files found matching current scan filters.
      </div>
    `;
    return;
  }

  wasters.slice(0, 6).forEach((f, idx) => {
    const card = document.createElement('div');
    card.className = 'culprit-card';
    
    const icon = getCategoryIcon(f.category);
    const safetyBadge = `<span class="badge badge-${f.safety.level}">${f.safety.badge}</span>`;

    card.innerHTML = `
      <div class="culprit-top">
        <div class="culprit-name-wrap">
          <span class="culprit-icon">${icon}</span>
          <div style="overflow:hidden;">
            <div class="culprit-name" title="${f.name}">${f.name}</div>
            <div class="culprit-meta-tags">
              <span class="badge badge-info">${f.category}</span>
              ${safetyBadge}
            </div>
          </div>
        </div>
        <div class="culprit-size-badge">${f.formatted_size}</div>
      </div>

      <div>
        <div style="font-size:11px; color:var(--text-muted); margin-bottom:4px;">LOCATION ON C: DRIVE</div>
        <div class="culprit-path" title="${f.path}">${f.path}</div>
      </div>

      <div class="culprit-actions">
        <div class="culprit-days">
          ⏳ Untouched for <strong>${f.days_dormant} days</strong>
        </div>
        <div class="culprit-btn-group">
          <button class="btn btn-delete btn-sm btn-delete-card ${f.safety.level === 'system' ? 'btn-disabled' : ''}" title="${f.safety.level === 'system' ? 'Protected Windows OS file' : 'Delete file (Move to Recycle Bin)'}">
            🗑️ Delete
          </button>
          <button class="btn btn-primary btn-sm btn-open-exp" title="Open in Windows File Explorer">
            📁 Reveal
          </button>
          <button class="btn btn-outline btn-sm btn-copy-path" title="Copy Path">
            📋
          </button>
        </div>
      </div>
    `;

    card.querySelector('.btn-open-exp').addEventListener('click', () => openInExplorer(f.path));
    card.querySelector('.btn-copy-path').addEventListener('click', () => copyToClipboard(f.path));
    
    const cardDeleteBtn = card.querySelector('.btn-delete-card');
    if (cardDeleteBtn && f.safety.level !== 'system') {
      cardDeleteBtn.addEventListener('click', () => promptDelete(f));
    }

    elements.topCulpritsGrid.appendChild(card);
  });
}

// Slide 4: Folder Hotspots & Categories
function renderSlide4HotspotsAndCategories() {
  const a = state.analytics;
  const folders = a.folder_distribution || [];
  elements.folderHotspotsList.innerHTML = '';

  const maxBytes = folders.length > 0 ? folders[0].bytes : 1;
  folders.slice(0, 6).forEach(f => {
    const pct = Math.round((f.bytes / maxBytes) * 100);
    const item = document.createElement('div');
    item.className = 'hotspot-item';
    item.innerHTML = `
      <div class="hotspot-header">
        <span class="hotspot-path" title="${f.folder}">${f.folder}</span>
        <span style="font-weight:700; color:var(--text-main);">${f.formatted} (${f.pct}%)</span>
      </div>
      <div class="hotspot-bar-wrap">
        <div class="hotspot-bar-fill" style="width: ${pct}%;"></div>
      </div>
    `;
    elements.folderHotspotsList.appendChild(item);
  });

  // Categories Chart & Chips
  const cats = a.category_distribution || [];
  elements.categoryChipsWrap.innerHTML = '';
  cats.forEach(c => {
    const chip = document.createElement('div');
    chip.className = 'cat-chip';
    chip.innerHTML = `
      <span>${c.icon}</span>
      <span>${c.category}:</span>
      <strong>${c.formatted}</strong>
    `;
    elements.categoryChipsWrap.appendChild(chip);
  });

  drawCategoryDonutChart(elements.categoryDistributionChart, cats);
}

// Slide 5: Roadmap
function renderSlide5Roadmap() {
  const a = state.analytics;
  elements.roadSafeGB.textContent = a.safe_formatted || '0 B';
  
  // Compute Review size (Media + VMs + Models)
  const cats = a.category_distribution || [];
  let reviewBytes = 0;
  cats.forEach(c => {
    if (['Media & Video', 'Virtual Machines & Disks', 'AI Models & Datasets'].includes(c.category)) {
      reviewBytes += c.bytes;
    }
  });
  elements.roadReviewGB.textContent = formatBytes(reviewBytes);
}

// Explorer Table Rendering
function renderTable() {
  let filtered = [...state.results];

  // Search filter
  if (state.searchTerm) {
    filtered = filtered.filter(f => 
      f.name.toLowerCase().includes(state.searchTerm) ||
      f.path.toLowerCase().includes(state.searchTerm) ||
      f.category.toLowerCase().includes(state.searchTerm)
    );
  }

  // Category filter
  if (state.selectedCategory !== 'ALL') {
    if (state.selectedCategory === 'SAFE_ONLY') {
      filtered = filtered.filter(f => f.safety.level === 'safe');
    } else {
      filtered = filtered.filter(f => f.category === state.selectedCategory);
    }
  }

  // Sorting
  filtered.sort((a, b) => {
    let valA = a[state.sortCol];
    let valB = b[state.sortCol];

    if (typeof valA === 'string') {
      valA = valA.toLowerCase();
      valB = valB.toLowerCase();
    }

    if (valA < valB) return state.sortDir === 'asc' ? -1 : 1;
    if (valA > valB) return state.sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  // Calculate stats
  const totalBytes = filtered.reduce((acc, f) => acc + f.size_bytes, 0);
  elements.showingCount.textContent = filtered.length.toLocaleString();
  elements.totalCount.textContent = state.results.length.toLocaleString();
  elements.showingSize.textContent = formatBytes(totalBytes);

  elements.dormantTableBody.innerHTML = '';
  elements.noResultsMsg.classList.toggle('hidden', filtered.length > 0);

  // Render Rows (capped at 500 for high DOM performance)
  filtered.slice(0, 500).forEach(f => {
    const row = document.createElement('tr');
    const icon = getCategoryIcon(f.category);

    row.innerHTML = `
      <td>
        <div class="file-cell" title="${f.name}">
          <span>${icon}</span>
          <span style="max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${f.name}</span>
        </div>
      </td>
      <td>
        <div class="path-cell" title="${f.path}">${f.path}</div>
      </td>
      <td class="size-cell">${f.formatted_size}</td>
      <td class="days-cell">${f.days_dormant} days</td>
      <td style="color:var(--text-muted); font-size:12px;">${f.mtime_str}</td>
      <td><span class="badge badge-info">${f.category}</span></td>
      <td>
        <span class="badge badge-${f.safety.level}">${f.safety.badge}</span>
        ${f.accessDenied ? '<span class="badge badge-caution btn-open-denied" style="margin-top:4px; display:inline-flex; cursor:pointer;" title="Access Denied: Click to open in File Explorer to delete manually">🔒 Open in Explorer</span>' : ''}
      </td>
      <td class="text-right">
        <div class="action-btns">
          <button class="btn btn-delete btn-sm btn-row-delete ${f.safety.level === 'system' ? 'btn-disabled' : ''}" title="${f.safety.level === 'system' ? 'Protected Windows OS file' : 'Delete file (Move to Recycle Bin)'}">
            🗑️
          </button>
          <button class="btn btn-primary btn-sm btn-row-open ${f.accessDenied ? 'btn-highlight-glow' : ''}" title="Open and highlight in Windows Explorer">
            📁
          </button>
          <button class="btn btn-secondary btn-sm btn-row-copy" title="Copy Path">
            📋
          </button>
          <button class="btn btn-outline btn-sm btn-row-info" title="View Details">
            ℹ️
          </button>
        </div>
      </td>
    `;

    const deniedBadge = row.querySelector('.btn-open-denied');
    if (deniedBadge) {
      deniedBadge.addEventListener('click', () => openInExplorer(f.path));
    }

    const rowDeleteBtn = row.querySelector('.btn-row-delete');
    if (rowDeleteBtn && f.safety.level !== 'system') {
      rowDeleteBtn.addEventListener('click', () => promptDelete(f, row));
    }

    row.querySelector('.btn-row-open').addEventListener('click', () => openInExplorer(f.path));
    row.querySelector('.btn-row-copy').addEventListener('click', () => copyToClipboard(f.path));
    row.querySelector('.btn-row-info').addEventListener('click', () => openFileModal(f));

    elements.dormantTableBody.appendChild(row);
  });
}

function updateSortingHeaders() {
  elements.dormantTable.querySelectorAll('th.sortable').forEach(th => {
    th.classList.remove('sorted-asc', 'sorted-desc');
    if (th.dataset.sort === state.sortCol) {
      th.classList.add(state.sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
    }
  });
}

function setCategoryFilter(category) {
  state.selectedCategory = category;
  elements.categoryFiltersRow.querySelectorAll('.cat-pill').forEach(pill => {
    pill.classList.toggle('active', pill.dataset.cat === category);
  });
  renderTable();
}

// Presentation Navigation Controls
function initSlideIndicators() {
  elements.slideIndicators.innerHTML = '';
  for (let i = 1; i <= state.totalSlides; i++) {
    const dot = document.createElement('div');
    dot.className = `indicator-dot ${i === 1 ? 'active' : ''}`;
    dot.dataset.slide = i;
    dot.addEventListener('click', () => goToSlide(i));
    elements.slideIndicators.appendChild(dot);
  }
}

function changeSlide(direction) {
  let next = state.currentSlide + direction;
  if (next > state.totalSlides) next = 1;
  if (next < 1) next = state.totalSlides;
  goToSlide(next);
}

function goToSlide(slideNum) {
  state.currentSlide = slideNum;
  document.querySelectorAll('.slides-container .slide').forEach(s => {
    s.classList.toggle('active', parseInt(s.dataset.slide) === slideNum);
  });

  document.querySelectorAll('.slide-indicators .indicator-dot').forEach(dot => {
    dot.classList.toggle('active', parseInt(dot.dataset.slide) === slideNum);
  });

  elements.slideNumberDisplay.textContent = `Slide ${slideNum} of ${state.totalSlides}`;

  // Redraw canvas if needed
  if (slideNum === 2) {
    drawHorizontalBarChart(elements.ageDistributionChart, state.analytics.age_distribution || []);
  } else if (slideNum === 4) {
    drawCategoryDonutChart(elements.categoryDistributionChart, state.analytics.category_distribution || []);
  }
}

function toggleAutoplay() {
  state.isAutoplay = !state.isAutoplay;
  elements.autoplayBtn.classList.toggle('active', state.isAutoplay);
  elements.autoplayIcon.textContent = state.isAutoplay ? '⏸' : '▶';

  if (state.isAutoplay) {
    state.autoplayInterval = setInterval(() => changeSlide(1), 7000);
    showToast('Autoplay presentation enabled (7s per slide)', '▶');
  } else {
    clearInterval(state.autoplayInterval);
    state.autoplayInterval = null;
    showToast('Autoplay paused', '⏸');
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(err => console.error(err));
  } else {
    document.exitFullscreen().catch(err => console.error(err));
  }
}

function switchView(viewName) {
  state.view = viewName;
  elements.viewBtnPresentation.classList.toggle('active', viewName === 'presentation');
  elements.viewBtnExplorer.classList.toggle('active', viewName === 'explorer');
  elements.presentationView.classList.toggle('hidden', viewName !== 'presentation');
  elements.explorerView.classList.toggle('hidden', viewName !== 'explorer');
}

// Windows File Explorer & Clipboard Actions
async function openInExplorer(path, mode = 'select') {
  if (!path) return;

  // 1. Always copy the full path to clipboard immediately
  try {
    navigator.clipboard.writeText(path);
  } catch (e) {}

  try {
    const res = await fetch(`${API_BASE}/api/open-explorer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, mode })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      const targetDesc = data.folder || getBasename(path);
      const actionMsg = data.message || (mode === 'folder' ? `Opened folder: ${targetDesc}` : `Selected file: ${getBasename(path)}`);
      showToast(`📁 ${actionMsg}. (If Explorer opened behind browser, check taskbar or press Alt+Tab)`, '📁', 6500);
    } else {
      showToast(data.error || 'Path copied to clipboard! Press Win+R, paste (Ctrl+V) and hit Enter to jump directly there.', '⚠️', 6000);
    }
  } catch (err) {
    showToast(`Path copied to clipboard! Press Win+R, paste (Ctrl+V) and press Enter: ${getBasename(path)}`, '📋', 7000);
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Path copied to clipboard!', '📋');
  }).catch(() => {
    showToast('Failed to copy path', '⚠️');
  });
}

// File Details Modal
function openFileModal(file) {
  state.selectedFile = file;
  elements.modalFileName.textContent = file.name;

  elements.modalBody.innerHTML = `
    <div class="modal-field">
      <div class="modal-label">Exact C: Drive File Path</div>
      <div class="modal-val-path">${file.path}</div>
    </div>

    <div class="modal-grid-2col">
      <div class="modal-field">
        <div class="modal-label">File Size</div>
        <div style="font-size:16px; font-weight:700;">${file.formatted_size} (${file.size_bytes.toLocaleString()} bytes)</div>
      </div>
      <div class="modal-field">
        <div class="modal-label">Inactivity Duration</div>
        <div style="font-size:16px; font-weight:700; color:var(--amber);">${file.days_dormant} days untouched</div>
      </div>
    </div>

    <div class="modal-grid-2col">
      <div class="modal-field">
        <div class="modal-label">Last Modified Date</div>
        <div>${file.mtime_str} (${file.days_since_mtime} days ago)</div>
      </div>
      <div class="modal-field">
        <div class="modal-label">Last Accessed Date</div>
        <div>${file.atime_str} (${file.days_since_atime} days ago)</div>
      </div>
    </div>

    <div class="modal-field">
      <div class="modal-label">Category & Classification</div>
      <div style="display:flex; gap:8px; align-items:center; margin-top:4px;">
        <span class="badge badge-info">${file.category}</span>
        <span class="badge badge-${file.safety.level}">${file.safety.badge}</span>
      </div>
    </div>

    <div class="modal-field">
      <div class="modal-label">Safety & Cleanup Recommendation</div>
      <div style="font-size:13px; color:var(--text-muted); background:var(--bg-card); padding:10px; border-radius:6px; border:1px solid var(--border-subtle);">
        ${file.safety.advice}
      </div>
    </div>
  `;

  if (file.safety && file.safety.level === 'system') {
    elements.modalDeleteBtn.classList.add('btn-disabled');
    elements.modalDeleteBtn.title = 'Windows System file - protected from deletion';
  } else {
    elements.modalDeleteBtn.classList.remove('btn-disabled');
    elements.modalDeleteBtn.title = 'Delete this file (Move to Recycle Bin)';
  }

  elements.fileModal.classList.remove('hidden');
}

function closeModal() {
  elements.fileModal.classList.add('hidden');
  state.selectedFile = null;
}

function closeDeleteModal() {
  elements.deleteModal.classList.add('hidden');
  state.pendingDeleteFile = null;
  state.pendingDeleteRow = null;
}

function promptDelete(file, rowElement = null) {
  if (file.safety && file.safety.level === 'system') {
    showToast('Cannot delete Windows System file. Operating system files are protected.', '🛡️', 4000);
    return;
  }

  if (state.skipDeleteConfirmation) {
    executeDelete(file, rowElement);
    return;
  }

  state.pendingDeleteFile = file;
  state.pendingDeleteRow = rowElement;

  elements.deleteModalFileName.textContent = file.name;
  elements.deleteModalFilePath.textContent = file.path;
  elements.deleteModalFileSize.textContent = file.formatted_size;
  elements.deleteModalFileDays.textContent = `${file.days_dormant} days untouched`;

  elements.deleteModal.classList.remove('hidden');
}

async function executeDelete(file, rowElement = null) {
  try {
    if (rowElement) {
      rowElement.classList.add('row-deleting');
    }

    const res = await fetch(`${API_BASE}/api/delete-file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: file.path, permanent: false })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`🗑️ Moved "${file.name}" to Windows Recycle Bin. Reclaimed ${file.formatted_size}!`, '🗑️', 4500);

      // Remove from results array
      const idx = state.results.findIndex(f => f.path.toLowerCase() === file.path.toLowerCase());
      if (idx !== -1) {
        state.results.splice(idx, 1);
      }

      // Update analytics and drive info from server
      if (data.analytics) state.analytics = data.analytics;
      if (data.drive_info) state.driveInfo = data.drive_info;

      // Close modal if deleting current modal file
      if (state.selectedFile && state.selectedFile.path.toLowerCase() === file.path.toLowerCase()) {
        closeModal();
      }

      // Re-render views
      renderAllViews();
    } else {
      if (rowElement) {
        rowElement.classList.remove('row-deleting');
      }

      // Mark file as access denied so the user sees direct guidance
      file.accessDenied = true;

      // Check if error is access denied / permissions
      const errStr = (data.error || '').toLowerCase();
      if (data.is_access_denied || errStr.includes('access is denied') || errStr.includes('permission') || res.status === 403) {
        showAccessDeniedGuidance(file, data.error);
      } else {
        showToast(data.error || 'Delete failed', '⚠️', 5000);
      }
      renderTable();
    }
  } catch (err) {
    if (rowElement) {
      rowElement.classList.remove('row-deleting');
    }
    file.accessDenied = true;
    const errStr = (err.message || '').toLowerCase();
    if (errStr.includes('access is denied') || errStr.includes('permission')) {
      showAccessDeniedGuidance(file, err.message);
    } else {
      showToast('Error deleting file: ' + err.message, '⚠️', 5000);
    }
    renderTable();
  }
}

function showAccessDeniedGuidance(file, errorMsg) {
  state.deniedFile = file;
  elements.deniedModalFileName.textContent = file.name;
  elements.deniedModalFilePath.textContent = file.path;
  elements.accessDeniedModal.classList.remove('hidden');
}

function closeAccessDeniedModal() {
  elements.accessDeniedModal.classList.add('hidden');
  state.deniedFile = null;
}

// Toast Notifications
let toastTimeout = null;
function showToast(msg, icon = 'ℹ️', duration = 3500) {
  elements.toastIcon.textContent = icon;
  elements.toastMessage.textContent = msg;
  elements.toastNotification.classList.remove('hidden');

  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    elements.toastNotification.classList.add('hidden');
  }, duration);
}

// Theme Handling
function initTheme() {
  const saved = localStorage.getItem('c_analyzer_theme') || 'dark';
  setTheme(saved);
}

function toggleTheme() {
  const current = document.body.classList.contains('theme-light') ? 'light' : 'dark';
  setTheme(current === 'light' ? 'dark' : 'light');
}

function setTheme(theme) {
  document.body.classList.remove('theme-light', 'theme-dark');
  document.body.classList.add(`theme-${theme}`);
  elements.themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
  localStorage.setItem('c_analyzer_theme', theme);

  // Redraw active charts to match palette
  if (state.currentSlide === 2) {
    drawHorizontalBarChart(elements.ageDistributionChart, state.analytics.age_distribution || []);
  } else if (state.currentSlide === 4) {
    drawCategoryDonutChart(elements.categoryDistributionChart, state.analytics.category_distribution || []);
  }
}

// Canvas Chart Renderers (Zero Dependencies, Self-Contained)
function drawHorizontalBarChart(canvas, data) {
  if (!canvas || !data || data.length === 0) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  const isLight = document.body.classList.contains('theme-light');
  const textColor = isLight ? '#334155' : '#94a3b8';

  const maxGb = Math.max(...data.map(d => d.gb || 0), 1);
  const barHeight = 22;
  const startY = 20;
  const rowGap = 42;
  const labelWidth = 110;
  const chartWidth = width - labelWidth - 90;

  data.forEach((d, i) => {
    const y = startY + (i * rowGap);
    const barW = Math.max(4, Math.round(((d.gb || 0) / maxGb) * chartWidth));

    // Label
    ctx.font = '600 12px sans-serif';
    ctx.fillStyle = textColor;
    ctx.textAlign = 'right';
    ctx.fillText(d.label, labelWidth - 12, y + 16);

    // Track background
    ctx.fillStyle = isLight ? '#e2e8f0' : '#1e293b';
    roundRect(ctx, labelWidth, y, chartWidth, barHeight, 4);
    ctx.fill();

    // Bar fill
    ctx.fillStyle = d.color || '#3b82f6';
    roundRect(ctx, labelWidth, y, barW, barHeight, 4);
    ctx.fill();

    // Value text
    ctx.textAlign = 'left';
    ctx.font = '700 12px sans-serif';
    ctx.fillStyle = isLight ? '#0f172a' : '#f8fafc';
    ctx.fillText(d.formatted, labelWidth + barW + 10, y + 16);
  });
}

function drawCategoryDonutChart(canvas, data) {
  if (!canvas || !data || data.length === 0) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  const centerX = width / 2;
  const centerY = height / 2;
  const outerRadius = Math.min(centerX, centerY) - 20;
  const innerRadius = outerRadius * 0.55;

  const totalBytes = data.reduce((acc, d) => acc + d.bytes, 0);
  if (totalBytes === 0) return;

  const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#6366f1', '#14b8a6', '#64748b'];

  let startAngle = -0.5 * Math.PI;

  data.slice(0, 8).forEach((d, i) => {
    const sliceAngle = (d.bytes / totalBytes) * 2 * Math.PI;
    const endAngle = startAngle + sliceAngle;

    ctx.beginPath();
    ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
    ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
    ctx.closePath();

    ctx.fillStyle = colors[i % colors.length];
    ctx.fill();

    startAngle = endAngle;
  });

  // Center Text
  const isLight = document.body.classList.contains('theme-light');
  ctx.fillStyle = isLight ? '#0f172a' : '#ffffff';
  ctx.font = '800 16px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(formatBytes(totalBytes), centerX, centerY + 2);

  ctx.fillStyle = isLight ? '#64748b' : '#94a3b8';
  ctx.font = '600 10px sans-serif';
  ctx.fillText('TOTAL WASTE', centerX, centerY + 18);
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

// Helpers
function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return '0 B';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

function getBasename(path) {
  const parts = path.split('\\');
  return parts[parts.length - 1];
}

function getCategoryIcon(cat) {
  const map = {
    'Installers & Setup': '📦',
    'Archives & Compressed': '🗄️',
    'Media & Video': '🎬',
    'Virtual Machines & Disks': '💻',
    'AI Models & Datasets': '🧠',
    'Development Caches': '🛠️',
    'System / Virtual Memory': '⚙️',
    'Documents & Data': '📄',
    'Other Files': '📁'
  };
  return map[cat] || '📁';
}
