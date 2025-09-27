// グローバル変数
let locations = [];
let currentEditingItem = null;

// DOM読み込み完了時の初期化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// アプリケーション初期化
function initializeApp() {
    setupEventListeners();
    loadLocations();
    showTab('search');
}

// イベントリスナーの設定
function setupEventListeners() {
    // タブ切り替え
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabName = e.currentTarget.dataset.tab;
            showTab(tabName);
        });
    });

    // 検索機能
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // アイテム追加フォーム
    document.getElementById('addItemForm').addEventListener('submit', handleAddItem);

    // ファイル選択
    document.getElementById('selectFileBtn').addEventListener('click', () => {
        document.getElementById('excelFile').click();
    });

    document.getElementById('excelFile').addEventListener('change', handleFileSelect);
    document.getElementById('importBtn').addEventListener('click', handleImport);

    // モーダル関連
    document.querySelector('.close').addEventListener('click', closeModal);
    document.getElementById('editItemForm').addEventListener('submit', handleEditItem);
    document.getElementById('deleteItemBtn').addEventListener('click', handleDeleteItem);

    // モーダル外クリックで閉じる
    document.getElementById('itemModal').addEventListener('click', (e) => {
        if (e.target.id === 'itemModal') {
            closeModal();
        }
    });
}

// タブ表示切り替え
function showTab(tabName) {
    // すべてのタブボタンとコンテンツを非アクティブに
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // 選択されたタブをアクティブに
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');

    // タブ固有の初期化処理
    if (tabName === 'locations') {
        displayLocations();
    } else if (tabName === 'add-item') {
        populateLocationSelect('locationSelect');
    }
}

// 場所データの読み込み
async function loadLocations() {
    try {
        const response = await fetch('/api/locations');
        if (!response.ok) throw new Error('場所データの取得に失敗しました');
        locations = await response.json();
    } catch (error) {
        console.error('Error loading locations:', error);
        showNotification('場所データの読み込みに失敗しました', 'error');
    }
}

// 場所選択肢の設定
function populateLocationSelect(selectId) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">場所を選択してください</option>';
    
    locations.forEach(location => {
        const option = document.createElement('option');
        option.value = location.id;
        option.textContent = location.name;
        select.appendChild(option);
    });
}

// 検索実行
async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    const resultsContainer = document.getElementById('searchResults');

    if (!query) {
        resultsContainer.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-info-circle"></i>
                <p>検索キーワードを入力してアイテムを探してください</p>
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>検索中...</p>
        </div>
    `;

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('検索に失敗しました');
        
        const data = await response.json();
        displaySearchResults(data);
    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>検索中にエラーが発生しました</p>
            </div>
        `;
    }
}

// 検索結果の表示
function displaySearchResults(data) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (data.items.length === 0 && data.locations.length === 0) {
        resultsContainer.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-search"></i>
                <p>検索結果が見つかりませんでした</p>
            </div>
        `;
        return;
    }

    let html = '';

    if (data.items.length > 0) {
        html += '<h3><i class="fas fa-box"></i> アイテム</h3>';
        data.items.forEach(item => {
            html += createItemCard(item);
        });
    }

    if (data.locations.length > 0) {
        html += '<h3><i class="fas fa-building"></i> 場所</h3>';
        data.locations.forEach(location => {
            html += `
                <div class="location-card" onclick="showLocationItems('${location.id}')">
                    <div class="location-name">
                        <i class="fas fa-map-marker-alt"></i>
                        ${location.name}
                    </div>
                    ${location.description ? `<div class="location-description">${location.description}</div>` : ''}
                    <span class="location-items-count">${location.items_count}個のアイテム</span>
                </div>
            `;
        });
    }

    resultsContainer.innerHTML = html;
}

// アイテムカードの作成
function createItemCard(item) {
    return `
        <div class="item-card" onclick="openItemModal('${item.id}')">
            <div class="item-name">${item.name}</div>
            <div class="item-location">${item.location_name || '場所不明'}</div>
            ${item.sub_location ? `<div class="item-sub-location">${item.sub_location}</div>` : ''}
            ${item.notes ? `<div class="item-notes">${item.notes}</div>` : ''}
        </div>
    `;
}

// 場所一覧の表示
function displayLocations() {
    const container = document.getElementById('locationsGrid');
    
    if (locations.length === 0) {
        container.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-building"></i>
                <p>場所データがありません</p>
            </div>
        `;
        return;
    }

    const html = locations.map(location => `
        <div class="location-card" onclick="showLocationItems('${location.id}')">
            <div class="location-name">
                <i class="fas fa-map-marker-alt"></i>
                ${location.name}
            </div>
            ${location.description ? `<div class="location-description">${location.description}</div>` : ''}
            <span class="location-items-count">${location.items_count || 0}個のアイテム</span>
        </div>
    `).join('');

    container.innerHTML = html;
}

// 特定場所のアイテム表示
async function showLocationItems(locationId) {
    try {
        const response = await fetch(`/api/locations/${locationId}`);
        if (!response.ok) throw new Error('場所データの取得に失敗しました');
        
        const location = await response.json();
        
        // 検索タブに切り替えて結果を表示
        showTab('search');
        
        const resultsContainer = document.getElementById('searchResults');
        let html = `<h3><i class="fas fa-map-marker-alt"></i> ${location.name}</h3>`;
        
        if (location.items.length === 0) {
            html += `
                <div class="welcome-message">
                    <i class="fas fa-box-open"></i>
                    <p>この場所にはアイテムがありません</p>
                </div>
            `;
        } else {
            location.items.forEach(item => {
                html += createItemCard(item);
            });
        }
        
        resultsContainer.innerHTML = html;
    } catch (error) {
        console.error('Error loading location items:', error);
        showNotification('場所のアイテム取得に失敗しました', 'error');
    }
}

// アイテム追加処理
async function handleAddItem(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('itemName').value,
        location_id: document.getElementById('locationSelect').value,
        sub_location: document.getElementById('subLocation').value,
        quantity: parseInt(document.getElementById('quantity').value) || 1,
        notes: document.getElementById('notes').value
    };

    try {
        const response = await fetch('/api/items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'アイテムの追加に失敗しました');
        }

        showNotification('アイテムが正常に追加されました', 'success');
        document.getElementById('addItemForm').reset();
        document.getElementById('quantity').value = 1;
        
    } catch (error) {
        console.error('Error adding item:', error);
        showNotification(error.message, 'error');
    }
}

// ファイル選択処理
function handleFileSelect(e) {
    const file = e.target.files[0];
    const fileName = document.getElementById('fileName');
    const importBtn = document.getElementById('importBtn');

    if (file) {
        fileName.textContent = file.name;
        importBtn.disabled = false;
    } else {
        fileName.textContent = '';
        importBtn.disabled = true;
    }
}

// インポート処理
async function handleImport() {
    const fileInput = document.getElementById('excelFile');
    const file = fileInput.files[0];
    const resultDiv = document.getElementById('importResult');

    if (!file) {
        showNotification('ファイルを選択してください', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    resultDiv.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>インポート中...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/import/excel', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'インポートに失敗しました');
        }

        resultDiv.innerHTML = `
            <div class="import-result success">
                <h4><i class="fas fa-check-circle"></i> インポート完了</h4>
                <p>場所: ${result.imported_locations}件</p>
                <p>アイテム: ${result.imported_items}件</p>
            </div>
        `;

        // データを再読み込み
        await loadLocations();
        showNotification('データのインポートが完了しました', 'success');

    } catch (error) {
        console.error('Import error:', error);
        resultDiv.innerHTML = `
            <div class="import-result error">
                <h4><i class="fas fa-exclamation-triangle"></i> インポートエラー</h4>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// アイテム詳細モーダルを開く
async function openItemModal(itemId) {
    try {
        const response = await fetch(`/api/items/${itemId}`);
        if (!response.ok) throw new Error('アイテムデータの取得に失敗しました');
        
        const item = await response.json();
        currentEditingItem = item;

        // モーダルにデータを設定
        document.getElementById('editItemId').value = item.id;
        document.getElementById('editItemName').value = item.name;
        document.getElementById('editSubLocation').value = item.sub_location || '';
        document.getElementById('editQuantity').value = item.quantity || 1;
        document.getElementById('editNotes').value = item.notes || '';

        // 場所選択肢を設定
        populateLocationSelect('editLocationSelect');
        document.getElementById('editLocationSelect').value = item.location_id;

        // モーダルを表示
        document.getElementById('itemModal').classList.add('show');

    } catch (error) {
        console.error('Error opening item modal:', error);
        showNotification('アイテム詳細の取得に失敗しました', 'error');
    }
}

// モーダルを閉じる
function closeModal() {
    document.getElementById('itemModal').classList.remove('show');
    currentEditingItem = null;
}

// アイテム編集処理
async function handleEditItem(e) {
    e.preventDefault();
    
    const itemId = document.getElementById('editItemId').value;
    const formData = {
        name: document.getElementById('editItemName').value,
        location_id: document.getElementById('editLocationSelect').value,
        sub_location: document.getElementById('editSubLocation').value,
        quantity: parseInt(document.getElementById('editQuantity').value) || 1,
        notes: document.getElementById('editNotes').value
    };

    try {
        const response = await fetch(`/api/items/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'アイテムの更新に失敗しました');
        }

        showNotification('アイテムが正常に更新されました', 'success');
        closeModal();
        
        // 検索結果を更新（現在の検索クエリがある場合）
        const searchInput = document.getElementById('searchInput');
        if (searchInput.value.trim()) {
            performSearch();
        }

    } catch (error) {
        console.error('Error updating item:', error);
        showNotification(error.message, 'error');
    }
}

// アイテム削除処理
async function handleDeleteItem() {
    if (!currentEditingItem) return;

    if (!confirm(`「${currentEditingItem.name}」を削除してもよろしいですか？`)) {
        return;
    }

    try {
        const response = await fetch(`/api/items/${currentEditingItem.id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'アイテムの削除に失敗しました');
        }

        showNotification('アイテムが正常に削除されました', 'success');
        closeModal();
        
        // 検索結果を更新
        const searchInput = document.getElementById('searchInput');
        if (searchInput.value.trim()) {
            performSearch();
        }

    } catch (error) {
        console.error('Error deleting item:', error);
        showNotification(error.message, 'error');
    }
}

// 通知表示
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

