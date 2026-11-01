"""GTPS 交互式知识图谱生成引擎。

基于 ECharts 5 Graph + 力导向布局，将 CausalNetwork 因果拓扑
与 GlobalEvent 地缘实体关联渲染为自闭合 HTML 字符串，
可直接通过 streamlit.components.v1.html(html, height=...) 嵌入。

模板注入采用"唯一注释 token + str.replace"策略，绕开花括号冲突。
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple
from typing import Any, Dict, List, Tuple

from ..core.models import CausalLink, CausalNode, DomainCategory
from ..causal_engine.causal_network import CausalNetwork


# ---------------------------------------------------------------------------
# 领域 → 颜色映射（暗黑磨砂主题调色盘）
# ---------------------------------------------------------------------------
_DOMAIN_COLOR_MAP: Dict[str, str] = {
    "TECHNOLOGY": "#8b5cf6",   # 科技 - 紫罗兰
    "ENERGY":     "#f59e0b",   # 能源 - 琥珀
    "POLITICS":   "#ef4444",   # 政治 - 警示红
    "ECONOMY":    "#10b981",   # 经济 - 翠绿
    "SOCIETY":    "#06b6d4",   # 社会 - 青色
    "ECOLOGY":    "#84cc16",   # 生态 - 青柠
}


# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 本地 ECharts 5.5.0 核心引擎（100% 自闭合，零外部 CDN 依赖，彻底根除白屏）
# ---------------------------------------------------------------------------
_LOCAL_ECHARTS_PATH = os.path.join(os.path.dirname(__file__), "echarts.min.js")
_EMBEDDED_ECHARTS_SCRIPT = ""
if os.path.exists(_LOCAL_ECHARTS_PATH):
    try:
        with open(_LOCAL_ECHARTS_PATH, "r", encoding="utf-8") as _f:
            _raw_js = _f.read()
            if len(_raw_js) > 500000:
                _EMBEDDED_ECHARTS_SCRIPT = f"<script>/* ECharts 5.5.0 Local Embedded Engine */\n{_raw_js}\n</script>"
    except Exception as _e:
        _EMBEDDED_ECHARTS_SCRIPT = ""

if not _EMBEDDED_ECHARTS_SCRIPT:
    _EMBEDDED_ECHARTS_SCRIPT = '<script src="https://registry.npmmirror.com/echarts/5.5.0/files/dist/echarts.min.js" onerror="this.onerror=null;this.src=\'https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js\';"></script>'



# ---------------------------------------------------------------------------
# HTML 模板 —— 因果网络图谱
# ---------------------------------------------------------------------------
_CAUSAL_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  /* st.html 直接注入主文档，不依赖 iframe 百分比高度；用 min-height 确保容器可见 */
  .gtps-container { display:flex; flex-direction:column; width:100%; min-height:(_HEIGHT_)px; background:#0e1117; font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif; }
  .gtps-toolbar {
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
    padding:8px 14px; background:rgba(22,27,34,0.75); border-bottom:1px solid rgba(255,255,255,0.08);
    gap:8px;
  }
  .gtps-title {
    color:#e6edf3; font-size:13px; font-weight:700; letter-spacing:0.04em;
    display:flex; align-items:center; gap:8px; flex-shrink:0;
  }
  .gtps-title span { color:#8b949e; font-weight:400; font-size:11px; }
  .gtps-graph-legend {
    display:flex; gap:6px; flex-wrap:wrap; align-items:center; justify-content:flex-end;
  }
  .gtps-lg-item {
    display:inline-flex !important; align-items:center; gap:5px; width:auto !important; flex:0 0 auto !important;
    background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.12);
    padding:3px 8px; border-radius:4px; font-size:11px; color:#c9d1d9; white-space:nowrap;
  }
  .gtps-lg-dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
  #gtps-graph-{{GRAPH_ID}} { width:100%; height:(_HEIGHT_)px; background:#0e1117; }
  @media (max-width: 768px) {
    .gtps-toolbar { padding:6px 10px; }
    .gtps-title { font-size:12px; }
    .gtps-title span { display:none; }
    .gtps-lg-item { padding:2px 6px; font-size:10px; }
  }
  .echarts-tooltip {
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;
    background:rgba(22,27,34,0.96) !important; border:1px solid rgba(139,148,158,0.25) !important;
    border-radius:8px !important; box-shadow:0 6px 20px rgba(0,0,0,0.55) !important;
    padding:12px 16px !important; color:#e6edf3 !important; max-width:320px !important;
    backdrop-filter:blur(10px);
  }
  .echarts-tooltip .gtps-tp-name { font-size:13px; font-weight:700; margin-bottom:6px; color:#ffffff; }
  .echarts-tooltip .gtps-tp-row { font-size:12px; color:#c9d1d9; margin:2px 0; line-height:1.5; }
  .echarts-tooltip .gtps-tp-row b { color:#8b949e; font-weight:600; margin-right:6px; }
  .echarts-tooltip .gtps-tp-desc { margin-top:8px; padding-top:8px; border-top:1px dashed rgba(139,148,158,0.25); font-size:11px; color:#a9b1bd; line-height:1.5; }
</style>
</head>
<body>
<div class="gtps-container">
  <div class="gtps-toolbar">
    <div class="gtps-title">GTPS 因果拓扑图谱 <span>Force-directed · 拖拽平移 · 滚轮缩放</span></div>
    <div id="gtps-graph-legend-{{GRAPH_ID}}" class="gtps-graph-legend"></div>
  </div>
  <div id="gtps-graph-{{GRAPH_ID}}" style="width:100%;height:(_HEIGHT_)px;min-height:480px;"></div>
</div>
(_ECHARTS_SCRIPT_TAG_)
<script>
(function(){
  var graphId = '{{GRAPH_ID}}';
  var nodes  = (_DATA_NODES_);
  var links  = (_DATA_LINKS_);
  var legendDom = document.getElementById('gtps-graph-legend-' + graphId);

  // --- 图例 ---
  var legendColors = {
    'TECHNOLOGY':'#8b5cf6','ENERGY':'#f59e0b','POLITICS':'#ef4444',
    'ECONOMY':'#10b981','SOCIETY':'#06b6d4','ECOLOGY':'#84cc16'
  };
  Object.keys(legendColors).forEach(function(k){
    var item = document.createElement('div');
    item.className = 'gtps-lg-item';
    item.innerHTML = '<span class="gtps-lg-dot" style="background:'+legendColors[k]+'"></span>'+k;
    legendDom.appendChild(item);
  });
  // 边颜色图例
  var edgeLegend = [
    {c:'#10b981', t:'正向强化'},
    {c:'#ef4444', t:'负向制约'}
  ];
  edgeLegend.forEach(function(e){
    var item = document.createElement('div');
    item.className = 'gtps-lg-item';
    item.innerHTML = '<span style="display:inline-block;width:14px;height:2px;background:'+e.c+
                    (e.t==='负向制约'?';border-top:2px dashed '+e.c+'':'')+'"></span>'+e.t;
    legendDom.appendChild(item);
  });

  var retryCount = 0;
  function initChart() {
    if (typeof echarts === 'undefined') {
      retryCount++;
      if (retryCount === 20) {
        // 如果 2 秒内 primary CDN 未就绪，动态注入备用 CDN
        var fbScript = document.createElement('script');
        fbScript.src = '(_ECHARTS_CDN_FALLBACK_)';
        document.head.appendChild(fbScript);
      }
      setTimeout(initChart, 100);
      return;
    }
    var chartDom = document.getElementById('gtps-graph-' + graphId);
    if (!chartDom) return;

    // 容器不可见（Streamlit Tab 未激活时为 display:none，尺寸为 0）则轮询等待，
    // 直到容器获得真实尺寸再初始化，避免以 0x0 初始化后 ResizeObserver 不触发
    if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
      setTimeout(initChart, 120);
      return;
    }

    // 强制显式指定渲染物理尺寸，彻底防御 Streamlit Tab 切换时的 display:none (0px x 0px) 问题
    var initWidth = chartDom.clientWidth || window.innerWidth || 900;
    var initHeight = (_HEIGHT_);
    var chart = echarts.init(chartDom, null, {
      renderer: 'canvas',
      width: initWidth,
      height: initHeight
    });

    // 动态生成 categories 列表（ECharts graph 在节点带 category 时必须在 series.categories 中显式定义）
    var categories = Object.keys(legendColors).map(function(k){ return { name: k }; });
    nodes.forEach(function(n){
      if (n.category && !categories.some(function(c){ return c.name === n.category; })) {
        categories.push({ name: n.category });
      }
    });

    // 赋予节点初始环形散布坐标，避免力导向初始全聚于原点或 NaN
    var cx = initWidth / 2;
    var cy = initHeight / 2;
    var totalNodes = nodes.length || 1;
    nodes.forEach(function(n, i){
      if (typeof n.x === 'undefined' || isNaN(n.x)) {
        var angle = (i / totalNodes) * 2 * Math.PI;
        var r = Math.min(cx, cy) * 0.52;
        n.x = cx + r * Math.cos(angle);
        n.y = cy + r * Math.sin(angle);
      }
    });

    var option = {
    backgroundColor: '#0e1117',
    tooltip: {
      trigger: 'item',
      className: 'echarts-tooltip',
      enterable: true,
      appendToBody: true,
      formatter: function(p){
        if(p.dataType === 'edge'){
          var src = nodes.find(function(n){ return n.id === p.data.source || n.name === p.data.source; });
          var tgt = nodes.find(function(n){ return n.id === p.data.target || n.name === p.data.target; });
          var wStr = (p.data.weight > 0 ? '+' : '') + p.data.weight.toFixed(2);
          var wClass = p.data.weight >= 0 ? '#10b981' : '#ef4444';
          var html = '<div class="gtps-tp-name">'+(src?src.name:p.data.source)+' → '+(tgt?tgt.name:p.data.target)+'</div>';
          html += '<div class="gtps-tp-row"><b>传导强度</b><span style="color:'+wClass+';font-weight:700">'+wStr+'</span></div>';
          html += '<div class="gtps-tp-row"><b>时滞</b>'+p.data.delay+' 个月</div>';
          html += '<div class="gtps-tp-desc">'+p.data.mechanism+'</div>';
          return html;
        } else {
          var html = '<div class="gtps-tp-name">'+p.data.name+'</div>';
          html += '<div class="gtps-tp-row"><b>节点 ID</b><span style="font-family:monospace">'+p.data.id+'</span></div>';
          html += '<div class="gtps-tp-row"><b>所属领域</b>'+p.data.domain+'</div>';
          html += '<div class="gtps-tp-row"><b>演进强度</b>'+p.data.value.toFixed(2)+' / 1.00</div>';
          html += '<div class="gtps-tp-desc">'+(p.data.description||'（无描述）')+'</div>';
          return html;
        }
      }
    },
    legend: [{
      type: 'scroll',
      data: Object.keys(legendColors),
      show: false
    }],
    series: [{
      name: '因果拓扑',
      type: 'graph',
      layout: 'force',
      categories: categories,
      data: nodes,
      links: links,
      roam: true,
      focusNodeAdjacency: true,
      draggable: true,
      force: {
        repulsion: 380,
        edgeLength: [80, 160],
        gravity: 0.12,
        friction: 0.6,
        layoutAnimation: true
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{b}',
        color: '#c9d1d9',
        fontSize: 11,
        fontFamily: '-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif'
      },
      edgeLabel: { show: false },
      lineStyle: {
        curveness: 0.08
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 },
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(255,255,255,0.2)' }
      },
      animationDurationUpdate: 600,
      animationEasingUpdate: 'quinticInOut'
    }]
  };

    chart.setOption(option);

    // 强力自愈：通过 ResizeObserver 与多重定时器，保证 Tab 切换瞬间立即唤醒重绘
    if (window.ResizeObserver) {
      var ro = new ResizeObserver(function() {
        if (chartDom.clientWidth > 0) {
          chart.resize({
            width: chartDom.clientWidth,
            height: (_HEIGHT_)
          });
        }
      });
      ro.observe(chartDom);
      ro.observe(document.body);
    }

    [150, 400, 800, 1500].forEach(function(delay) {
      setTimeout(function() {
        if (chart) {
          chart.resize({
            width: chartDom.clientWidth || window.innerWidth || 900,
            height: (_HEIGHT_)
          });
        }
      }, delay);
    });

    window.addEventListener('resize', function(){
      if (chart) chart.resize();
    });
  }
  initChart();
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTML 模板 —— 事件-实体知识图谱
# ---------------------------------------------------------------------------
_ENTITY_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  /* st.html 直接注入主文档，不依赖 iframe 百分比高度 */
  #gtps-entity-{{GRAPH_ID}} { width:100%; height:(_HEIGHT_)px; background:#0e1117; }
  .gtps-title-e {
    position:absolute; top:12px; left:16px; z-index:10;
    color:#e6edf3; font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;
    font-size:13px; font-weight:700; letter-spacing:0.06em;
  }
  .gtps-title-e span { color:#8b949e; font-weight:400; margin-left:8px; font-size:11px; }
  .echarts-tooltip {
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;
    background:rgba(22,27,34,0.96) !important;
    border:1px solid rgba(139,148,158,0.25) !important;
    border-radius:8px !important;
    box-shadow:0 6px 20px rgba(0,0,0,0.55) !important;
    padding:14px 18px !important;
    color:#e6edf3 !important;
    max-width:340px !important;
    backdrop-filter:blur(10px);
  }
  .echarts-tooltip .tp-name { font-size:14px; font-weight:700; margin-bottom:6px; color:#ffffff; }
  .echarts-tooltip .tp-row { font-size:12px; color:#c9d1d9; margin:3px 0; line-height:1.55; }
  .echarts-tooltip .tp-row b { color:#8b949e; font-weight:600; margin-right:6px; }
  .echarts-tooltip .tp-desc { margin-top:10px; padding-top:10px; border-top:1px dashed rgba(139,148,158,0.25); font-size:12px; color:#a9b1bd; line-height:1.6; }
</style>
</head>
<body>
<div style="position:relative;width:100%;height:(_HEIGHT_)px;">
  <div class="gtps-title-e">GTPS 事件-实体关联图谱 <span>星形拓扑 · 中心节点 = 事件</span></div>
  <div id="gtps-entity-{{GRAPH_ID}}" style="width:100%;height:(_HEIGHT_)px;"></div>
</div>
(_ECHARTS_SCRIPT_TAG_)
<script>
(function(){
  var graphId = '{{GRAPH_ID}}';
  var nodes  = (_DATA_NODES_);
  var links  = (_DATA_LINKS_);

  function initChart() {
    if (typeof echarts === 'undefined') {
      setTimeout(initChart, 100);
      return;
    }
    var chartDom = document.getElementById('gtps-entity-' + graphId);
    if (!chartDom) return;

    // 容器不可见（Tab 未激活 display:none，尺寸为 0）则轮询等待真实尺寸
    if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
      setTimeout(initChart, 120);
      return;
    }

    var initWidth = chartDom.clientWidth || window.innerWidth || 900;
    var initHeight = (_HEIGHT_);
    var chart = echarts.init(chartDom, null, {
      renderer: 'canvas',
      width: initWidth,
      height: initHeight
    });

    var categoryMap = {};
    nodes.forEach(function(n){
      if (n.category) categoryMap[n.category] = true;
    });
    var categories = Object.keys(categoryMap).map(function(k){ return { name: k }; });
    if (categories.length === 0) categories = [{ name: 'DEFAULT' }];

    var cx = initWidth / 2;
    var cy = initHeight / 2;
    var totalNodes = nodes.length || 1;
    nodes.forEach(function(n, i){
      if (typeof n.x === 'undefined' || isNaN(n.x)) {
        var angle = (i / totalNodes) * 2 * Math.PI;
        var r = Math.min(cx, cy) * 0.52;
        n.x = cx + r * Math.cos(angle);
        n.y = cy + r * Math.sin(angle);
      }
    });

    var option = {
    backgroundColor: '#0e1117',
    tooltip: {
      trigger: 'item',
      className: 'echarts-tooltip',
      enterable: true,
      appendToBody: true,
      formatter: function(p){
        if(p.dataType === 'edge'){
          var src = nodes.find(function(n){ return n.id === p.data.source || n.name === p.data.source; });
          var tgt = nodes.find(function(n){ return n.id === p.data.target || n.name === p.data.target; });
          var html = '<div class="tp-name">'+(src?src.name:p.data.source)+' ⇄ '+(tgt?tgt.name:p.data.target)+'</div>';
          return html;
        } else {
          var html = '<div class="tp-name">'+p.data.name+'</div>';
          if(p.data.category !== undefined){
            html += '<div class="tp-row"><b>类别</b>'+p.data.category+'</div>';
          }
          if(p.data.kind !== undefined){
            html += '<div class="tp-row"><b>类型</b>'+p.data.kind+'</div>';
          }
          if(p.data.impact !== undefined){
            html += '<div class="tp-row"><b>冲击强度</b>'+p.data.impact.toFixed(2)+'</div>';
          }
          if(p.data.description){
            html += '<div class="tp-desc">'+p.data.description+'</div>';
          }
          return html;
        }
      }
    },
    series: [{
      name: '事件-实体关联',
      type: 'graph',
      layout: 'force',
      categories: categories,
      data: nodes,
      links: links,
      roam: true,
      focusNodeAdjacency: true,
      draggable: true,
      force: {
        repulsion: 400,
        edgeLength: [80, 160],
        gravity: 0.12,
        friction: 0.6
      },
      label: {
        show: true,
        position: 'right',
        color: '#c9d1d9',
        fontSize: 11,
        fontFamily: '-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif'
      },
      lineStyle: {
        curveness: 0.05,
        opacity: 0.55
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 3, opacity: 1 },
        itemStyle: { shadowBlur: 18, shadowColor: 'rgba(255,255,255,0.18)' }
      },
      animationDurationUpdate: 500,
      animationEasingUpdate: 'quinticInOut'
    }]
  };

    chart.setOption(option);

    // 强力自愈：通过 ResizeObserver 与多重定时器，保证 Tab 切换瞬间立即唤醒重绘
    if (window.ResizeObserver) {
      var ro = new ResizeObserver(function() {
        if (chartDom.clientWidth > 0) {
          chart.resize({
            width: chartDom.clientWidth,
            height: (_HEIGHT_)
          });
        }
      });
      ro.observe(chartDom);
      ro.observe(document.body);
    }

    [150, 400, 800, 1500].forEach(function(delay) {
      setTimeout(function() {
        if (chart) {
          chart.resize({
            width: chartDom.clientWidth || window.innerWidth || 900,
            height: (_HEIGHT_)
          });
        }
      }, delay);
    });

    window.addEventListener('resize', function(){
      if (chart) chart.resize();
    });
  }
  initChart();
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 实体提取 —— 预定义地缘 / 机构 / 产业词表
# ---------------------------------------------------------------------------
_ENTITY_KEYWORDS: Dict[str, List[Tuple[str, str]]] = {
    "地缘国家": [
        ("美国", "地缘国家"), ("中国", "地缘国家"), ("俄罗斯", "地缘国家"),
        ("乌克兰", "地缘国家"), ("以色列", "地缘国家"), ("伊朗", "地缘国家"),
        ("沙特", "地缘国家"), ("中东", "地缘区域"), ("欧盟", "超国家组织"),
        ("北约", "军事联盟"), ("霍尔木兹海峡", "战略咽喉"),
        ("红海", "战略水道"), ("亚速海", "战略区域"),
        ("加沙", "冲突热点"), ("朝鲜", "地缘国家"),
    ],
    "关键机构": [
        ("美联储", "金融机构"), ("OPEC", "能源组织"),
        ("欧佩克", "能源组织"), ("WTO", "贸易组织"),
        ("联合国", "国际组织"), ("IMF", "金融机构"),
        ("世界银行", "金融机构"), ("欧盟委员会", "超国家机构"),
    ],
    "关键产业": [
        ("英伟达", "半导体企业"), ("台积电", "半导体企业"),
        ("三星", "半导体企业"), ("英特尔", "半导体企业"),
        ("华为", "科技企业"), ("特斯拉", "新能源企业"),
        ("石油", "能源产业"), ("天然气", "能源产业"),
        ("稀土", "关键矿产"), ("锂矿", "关键矿产"),
        ("光刻机", "关键设备"), ("大模型", "AI 产业"),
        ("数据中心", "数字基础设施"),
    ],
}


def _build_entity_matcher() -> List[Tuple[str, str]]:
    """将多层词表拍平为 (keyword, kind) 列表，并按长度降序排序以优先匹配长词。"""
    flat: List[Tuple[str, str]] = []
    for cat, items in _ENTITY_KEYWORDS.items():
        for kw, kind in items:
            flat.append((kw, kind))
    flat.sort(key=lambda x: len(x[0]), reverse=True)
    return flat


# 模块级缓存
_ENTITY_MATCHER = _build_entity_matcher()


# ---------------------------------------------------------------------------
# 核心函数
# ---------------------------------------------------------------------------
def render_causal_graph_html(
    causal_net: CausalNetwork,
    highlight_loops: bool = False,
    height: int = 580,
) -> str:
    """将 CausalNetwork 渲染为 ECharts Graph 自闭合 HTML 字符串。

    Args:
        causal_net: GTPS 因果网络实例
        highlight_loops: 是否对参与反馈环的节点叠加金色发光边框
        height: 渲染容器像素高度

    Returns:
        可直接注入 streamlit.components.v1.html 的完整 HTML
    """
    # --- 节点数据 ---
    loop_nodes: set[str] = set()
    if highlight_loops:
        for loop in causal_net.find_feedback_loops():
            for nid in loop:
                loop_nodes.add(nid)

    nodes_data: List[Dict[str, Any]] = []
    for nid, node in causal_net.nodes_data.items():
        domain_upper = node.domain.value.upper() if node.domain else "TECHNOLOGY"
        color = _DOMAIN_COLOR_MAP.get(domain_upper, "#8b949e")
        node_entry: Dict[str, Any] = {
            "id": node.node_id,
            "name": node.name,
            "category": domain_upper,
            "symbolSize": int(28 + node.intensity * 32),
            "value": round(node.intensity, 2),
            "description": node.description,
            "domain": domain_upper,
            "itemStyle": {
                "color": color,
                "borderColor": color,
                "borderWidth": 1,
            },
        }
        if nid in loop_nodes:
            node_entry["itemStyle"]["borderColor"] = "#f59e0b"
            node_entry["itemStyle"]["borderWidth"] = 3
            node_entry["itemStyle"]["shadowColor"] = "#f59e0b"
            node_entry["itemStyle"]["shadowBlur"] = 12
        nodes_data.append(node_entry)

    # --- 边数据 ---
    links_data: List[Dict[str, Any]] = []
    for (src_id, tgt_id), link in causal_net.links_data.items():
        is_positive = link.weight > 0
        edge_color = "#10b981" if is_positive else "#ef4444"
        edge_type = "solid" if is_positive else "dashed"
        width = max(1.5, min(6.0, abs(link.weight) * 5.0))
        links_data.append({
            "source": src_id,
            "target": tgt_id,
            "weight": round(link.weight, 4),
            "delay": link.delay_months,
            "mechanism": link.mechanism,
            "lineStyle": {
                "color": edge_color,
                "type": edge_type,
                "width": width,
                "opacity": 0.75,
            },
            "symbol": ["none", "arrow"],
            "symbolSize": 8,
        })

    return _render(
        template=_CAUSAL_TEMPLATE,
        nodes_data=nodes_data,
        links_data=links_data,
        height=height,
        graph_id="causal",
    )


def render_entity_knowledge_graph_html(
    events: list,
    height: int = 580,
) -> str:
    """从 GlobalEvent 列表构建"事件 ➔ 实体"星形关联网络。

    Args:
        events: GlobalEvent 实例列表（collector 模块产物）
        height: 渲染容器像素高度

    Returns:
        自闭合 HTML 字符串
    """
    # --- 收集所有事件 ---
    nodes_data: List[Dict[str, Any]] = []
    links_data: List[Dict[str, Any]] = []
    seen_entities: set[str] = set()

    for idx, evt in enumerate(events):
        evt_id = f"evt_{idx}"
        evt_domain = evt.domain.value.upper() if evt.domain else "UNKNOWN"
        evt_color = _DOMAIN_COLOR_MAP.get(evt_domain, "#8b949e")

        nodes_data.append({
            "id": evt_id,
            "name": evt.title[:32] + ("…" if len(evt.title) > 32 else ""),
            "category": evt_domain,
            "kind": "EVENT",
            "symbolSize": int(38 + evt.impact_level * 24),
            "impact": evt.impact_level,
            "description": (evt.summary or "")[:200],
            "itemStyle": {
                "color": evt_color,
                "borderColor": "#ffffff",
                "borderWidth": 2,
            },
        })

        # --- 提取实体 ---
        haystack = (evt.title or "") + " " + (evt.summary or "")
        matched: set[str] = set()
        for kw, kind in _ENTITY_MATCHER:
            if kw in haystack and kw not in matched:
                matched.add(kw)
                ent_id = f"ent_{kw}"
                if ent_id not in seen_entities:
                    seen_entities.add(ent_id)
                    ent_color = _entity_color_for(kind)
                    nodes_data.append({
                        "id": ent_id,
                        "name": kw,
                        "category": "ENTITY",
                        "kind": kind,
                        "symbolSize": 26,
                        "description": f"识别为【{kind}】",
                        "itemStyle": {
                            "color": ent_color,
                            "borderColor": ent_color,
                            "borderWidth": 1,
                        },
                    })
                links_data.append({
                    "source": evt_id,
                    "target": ent_id,
                    "lineStyle": {
                        "color": "#555e6b",
                        "width": 1.0,
                        "opacity": 0.5,
                        "type": "solid",
                    },
                    "symbol": ["none", "none"],
                    "symbolSize": 0,
                })

    if not nodes_data:
        nodes_data.append({
            "id": "empty",
            "name": "（无事件数据）",
            "category": "EMPTY",
            "symbolSize": 28,
            "itemStyle": {"color": "#555e6b"},
        })

    return _render(
        template=_ENTITY_TEMPLATE,
        nodes_data=nodes_data,
        links_data=links_data,
        height=height,
        graph_id="entity",
    )


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------
def _entity_color_for(kind: str) -> str:
    """按实体类别返回稳定的颜色。"""
    if "地缘" in kind or kind == "战略咽喉" or kind == "战略区域" or kind == "冲突热点" or kind == "战略水道":
        return "#06b6d4"    # 青色 - 地缘
    if kind in ("超国家组织", "军事联盟", "国际组织"):
        return "#a78bfa"    # 浅紫 - 组织
    if "机构" in kind or "金融" in kind or "能源组织" in kind or "贸易组织":
        return "#f59e0b"    # 琥珀 - 机构
    if "企业" in kind:
        return "#10b981"    # 翠绿 - 企业
    if "矿产" in kind or "能源产业" in kind or "关键设备" in kind:
        return "#f97316"    # 橙色 - 产业
    return "#8b949e"        # 默认灰


def _render(
    template: str,
    nodes_data: List[Dict[str, Any]],
    links_data: List[Dict[str, Any]],
    height: int,
    graph_id: str,
) -> str:
    """通用模板渲染 —— token replace 注入 JSON，绕开花括号冲突。"""
    nodes_json = json.dumps(nodes_data, ensure_ascii=False, separators=(",", ":"))
    links_json = json.dumps(links_data, ensure_ascii=False, separators=(",", ":"))

    html = template
    html = html.replace("{{GRAPH_ID}}", graph_id)
    html = html.replace("(_ECHARTS_SCRIPT_TAG_)", _EMBEDDED_ECHARTS_SCRIPT)
    html = html.replace("(_DATA_NODES_)", nodes_json)
    html = html.replace("(_DATA_LINKS_)", links_json)
    html = html.replace("(_HEIGHT_)", str(height))
    return html
