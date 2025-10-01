// 全局变量
let allAtoms = [];
let filteredAtoms = [];
let currentPage = 1;
const itemsPerPage = 10;

// 加载数据
fetch('data.json')
    .then(response => response.json())
    .then(data => {
        allAtoms = data.atoms;
        filteredAtoms = [...allAtoms];

        // 初始化页面
        initStats(data.stats, data.report);
        initTypeChart(data.report.type_distribution);
        initTypeFilter(data.report.type_distribution);
        initTimeline();
        renderAtoms();
    })
    .catch(error => {
        console.error('加载数据失败:', error);
        alert('加载数据失败，请确保 data.json 文件存在');
    });

// 初始化统计概览
function initStats(stats, report) {
    document.getElementById('total-atoms').textContent = report.total_atoms;
    document.getElementById('cost').textContent = stats.estimated_cost;
    document.getElementById('quality').textContent = report.quality_score;
}

// 初始化类型分布图
function initTypeChart(typeDistribution) {
    const chartContainer = document.getElementById('type-chart');
    const total = Object.values(typeDistribution).reduce((a, b) => a + b, 0);
    const maxCount = Math.max(...Object.values(typeDistribution));

    Object.entries(typeDistribution)
        .sort((a, b) => b[1] - a[1])
        .forEach(([type, count]) => {
            const percentage = (count / maxCount) * 100;

            const barDiv = document.createElement('div');
            barDiv.className = 'chart-bar';
            barDiv.innerHTML = `
                <div class="chart-label">${type}</div>
                <div class="chart-bar-container">
                    <div class="chart-bar-fill" style="width: ${percentage}%">
                        ${count}个
                    </div>
                </div>
                <div class="chart-count">${(count/total*100).toFixed(1)}%</div>
            `;

            // 点击柱状图筛选
            barDiv.style.cursor = 'pointer';
            barDiv.addEventListener('click', () => {
                document.getElementById('type-filter').value = type;
                applyFilters();
            });

            chartContainer.appendChild(barDiv);
        });
}

// 初始化类型筛选器
function initTypeFilter(typeDistribution) {
    const select = document.getElementById('type-filter');
    Object.keys(typeDistribution).forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        select.appendChild(option);
    });
}

// 初始化时间轴
function initTimeline() {
    const container = document.getElementById('timeline-container');
    const maxTime = Math.max(...allAtoms.map(a => a.end_ms));

    allAtoms.forEach(atom => {
        const marker = document.createElement('div');
        marker.className = 'timeline-marker';
        marker.dataset.id = atom.atom_id;
        marker.style.left = `${(atom.start_ms / maxTime) * 100}%`;
        marker.title = `${atom.atom_id}: ${atom.type}`;

        marker.addEventListener('click', () => {
            showDetail(atom);
        });

        container.appendChild(marker);
    });
}

// 渲染原子列表
function renderAtoms() {
    const container = document.getElementById('atoms-container');
    container.innerHTML = '';

    // 计算分页
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageAtoms = filteredAtoms.slice(start, end);

    // 渲染原子卡片
    pageAtoms.forEach(atom => {
        const card = createAtomCard(atom);
        container.appendChild(card);
    });

    // 更新计数和分页
    document.getElementById('filtered-count').textContent = filteredAtoms.length;
    updatePagination();
}

// 创建原子卡片
function createAtomCard(atom) {
    const card = document.createElement('div');
    card.className = 'atom-card';

    // 截断文本
    const shortText = atom.merged_text.length > 100
        ? atom.merged_text.substring(0, 100) + '...'
        : atom.merged_text;

    card.innerHTML = `
        <div class="atom-header">
            <span class="atom-id">${atom.atom_id}</span>
            <span class="atom-time">[${atom.start_time} - ${atom.end_time}]</span>
            <span class="atom-duration">${atom.duration_seconds.toFixed(1)}秒</span>
            <span class="atom-type type-${atom.type}">${atom.type}</span>
        </div>
        <div class="atom-text">${shortText}</div>
    `;

    card.addEventListener('click', () => showDetail(atom));

    return card;
}

// 显示详情弹窗
function showDetail(atom) {
    const modal = document.getElementById('detail-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');

    title.textContent = `原子 ${atom.atom_id}`;

    body.innerHTML = `
        <div class="detail-row">
            <div class="detail-label">时间范围</div>
            <div class="detail-value">${atom.start_time} - ${atom.end_time} (${atom.duration_seconds.toFixed(1)}秒)</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">类型</div>
            <div class="detail-value"><span class="atom-type type-${atom.type}">${atom.type}</span></div>
        </div>
        <div class="detail-row">
            <div class="detail-label">完整性</div>
            <div class="detail-value">${atom.completeness}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">来源字幕</div>
            <div class="detail-value">#${atom.source_utterance_ids[0]} - #${atom.source_utterance_ids[atom.source_utterance_ids.length-1]} (共${atom.source_utterance_ids.length}条)</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">完整文本</div>
            <div class="detail-value full-text">${atom.merged_text}</div>
        </div>
    `;

    modal.style.display = 'block';
}

// 应用筛选
function applyFilters() {
    const typeFilter = document.getElementById('type-filter').value;
    const durationFilter = document.getElementById('duration-filter').value;
    const searchText = document.getElementById('search-input').value.toLowerCase();

    filteredAtoms = allAtoms.filter(atom => {
        // 类型筛选
        if (typeFilter !== 'all' && atom.type !== typeFilter) {
            return false;
        }

        // 时长筛选
        if (durationFilter !== 'all') {
            const duration = atom.duration_seconds;
            if (durationFilter === 'short' && duration >= 30) return false;
            if (durationFilter === 'medium' && (duration < 30 || duration >= 300)) return false;
            if (durationFilter === 'long' && duration < 300) return false;
        }

        // 文本搜索
        if (searchText && !atom.merged_text.toLowerCase().includes(searchText)) {
            return false;
        }

        return true;
    });

    currentPage = 1;
    renderAtoms();
}

// 更新分页
function updatePagination() {
    const totalPages = Math.ceil(filteredAtoms.length / itemsPerPage);

    document.getElementById('page-info').textContent =
        `第 ${currentPage} 页 / 共 ${totalPages} 页`;

    document.getElementById('prev-page').disabled = currentPage === 1;
    document.getElementById('next-page').disabled = currentPage === totalPages || totalPages === 0;
}

// 事件监听
document.getElementById('type-filter').addEventListener('change', applyFilters);
document.getElementById('duration-filter').addEventListener('change', applyFilters);
document.getElementById('search-input').addEventListener('input', applyFilters);

document.getElementById('prev-page').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        renderAtoms();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});

document.getElementById('next-page').addEventListener('click', () => {
    const totalPages = Math.ceil(filteredAtoms.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderAtoms();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});

// 关闭弹窗
document.querySelector('.close').addEventListener('click', () => {
    document.getElementById('detail-modal').style.display = 'none';
});

window.addEventListener('click', (event) => {
    const modal = document.getElementById('detail-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});
