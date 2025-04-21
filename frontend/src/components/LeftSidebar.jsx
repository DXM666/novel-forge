import React, { useState } from 'react';
import KnowledgeGraphView from './KnowledgeGraphView';

const defaultCharacters = [
  { name: 'John Carter', role: 'Protagonist' },
  { name: 'Sarah Connor', role: 'Antagonist' },
];
const defaultLocations = [
  { name: 'New Alexandria', desc: 'Futuristic city' },
];
const defaultTimeline = [
  { title: 'Chapter 1', desc: 'The Awakening' },
  { title: 'Chapter 2', desc: 'First Contact' },
];


const LeftSidebar = ({ visible, toggleLeft, characters: propCharacters = [], locations: propLocations = [], timeline: propTimeline = [], onCharactersChange, onLocationsChange, onTimelineChange }) => {
  const [kgData, setKgData] = useState(null);
  const [loading, setLoading] = useState(false);
  // 状态以props为主，内部仅作临时编辑
  const [characters, setCharacters] = useState(propCharacters.length ? propCharacters : defaultCharacters);
  const [locations, setLocations] = useState(propLocations.length ? propLocations : defaultLocations);
  const [timeline, setTimeline] = useState(propTimeline.length ? propTimeline : defaultTimeline);

  // 监听props变化，保持同步
  React.useEffect(() => { setCharacters(propCharacters.length ? propCharacters : defaultCharacters); }, [propCharacters]);
  React.useEffect(() => { setLocations(propLocations.length ? propLocations : defaultLocations); }, [propLocations]);
  React.useEffect(() => { setTimeline(propTimeline.length ? propTimeline : defaultTimeline); }, [propTimeline]);

  // 弹窗状态
  const [modal, setModal] = useState({ open: false, type: '', idx: null });
  const [modalData, setModalData] = useState({ name: '', desc: '', role: '' });

  const novelId = 'test_novel';

  const fetchKnowledgeGraph = async () => {
    setLoading(true);
    setKgData(null);
    try {
      const res = await fetch(`http://localhost:8000/api/knowledge-graph/${novelId}`);
      const data = await res.json();
      setKgData(data);
    } catch {
      setKgData({ error: '获取失败，请检查后端服务' });
    }
    setLoading(false);
  };

  // 通用弹窗打开
  const openModal = (type, idx = null) => {
    setModal({ open: true, type, idx });
    if (type === 'character') {
      setModalData(idx !== null ? characters[idx] : { name: '', role: '' });
    } else if (type === 'location') {
      setModalData(idx !== null ? locations[idx] : { name: '', desc: '' });
    } else if (type === 'timeline') {
      setModalData(idx !== null ? timeline[idx] : { title: '', desc: '' });
    }
  };
  // 通用弹窗关闭
  const closeModal = () => {
    setModal({ open: false, type: '', idx: null });
    setModalData({ name: '', desc: '', role: '' });
  };
  // 通用保存
  const handleSave = () => {
    if (modal.type === 'character') {
      const arr = [...characters];
      if (modal.idx !== null) arr[modal.idx] = modalData;
      else arr.push(modalData);
      setCharacters(arr);
      if (onCharactersChange) onCharactersChange(arr);
    } else if (modal.type === 'location') {
      const arr = [...locations];
      if (modal.idx !== null) arr[modal.idx] = modalData;
      else arr.push(modalData);
      setLocations(arr);
      if (onLocationsChange) onLocationsChange(arr);
    } else if (modal.type === 'timeline') {
      const arr = [...timeline];
      if (modal.idx !== null) arr[modal.idx] = modalData;
      else arr.push(modalData);
      setTimeline(arr);
      if (onTimelineChange) onTimelineChange(arr);
    }
    closeModal();
  };
  // 通用删除
  const handleDelete = (type, idx) => {
    if (type === 'character') {
      const arr = characters.filter((_, i) => i !== idx);
      setCharacters(arr);
      if (onCharactersChange) onCharactersChange(arr);
    } else if (type === 'location') {
      const arr = locations.filter((_, i) => i !== idx);
      setLocations(arr);
      if (onLocationsChange) onLocationsChange(arr);
    } else if (type === 'timeline') {
      const arr = timeline.filter((_, i) => i !== idx);
      setTimeline(arr);
      if (onTimelineChange) onTimelineChange(arr);
    }
  };

  return (
    <>
      <div id="leftSidebar" className={`sidebar-transition w-64 bg-indigo-900 text-white flex-shrink-0 overflow-y-auto ${visible ? '' : 'hidden'}`}>
        <div className="p-4 border-b border-indigo-800">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Story Elements</h2>
            <button onClick={toggleLeft} className="text-gray-300 hover:text-white">
              <i className={`fas ${visible ? 'fa-chevron-left' : 'fa-chevron-right'}`}></i>
            </button>
          </div>
          <div className="mt-4">
            <button
              className="w-full px-3 py-2 bg-indigo-600 hover:bg-indigo-700 rounded text-white font-medium mb-2"
              onClick={fetchKnowledgeGraph}
              disabled={loading}
            >
              {loading ? '加载中...' : '获取知识图谱'}
            </button>
            {/* 知识图谱可视化展示 */}
            {kgData && Array.isArray(kgData.elements) ? (
              <KnowledgeGraphView elements={kgData.elements} />
            ) : kgData ? (
              <pre className="bg-indigo-950 text-indigo-100 p-2 text-xs rounded overflow-x-auto max-h-60 mt-2">
                {JSON.stringify(kgData, null, 2)}
              </pre>
            ) : null}
            <div className="relative mt-4">
              <input type="text" placeholder="Search elements..." className="w-full bg-indigo-800 text-white px-3 py-2 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <i className="fas fa-search absolute right-3 top-2.5 text-gray-400"></i>
            </div>
          </div>
        </div>
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-indigo-200">Characters</h3>
            <button className="text-indigo-300 hover:text-white" onClick={() => openModal('character')}><i className="fas fa-plus"></i></button>
          </div>
          <div className="space-y-2">
            {characters.map((c, idx) => (
              <div key={idx} className="bg-indigo-800 rounded-md p-2 relative group flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center"><i className="fas fa-user text-sm"></i></div>
                  <div><p className="font-medium">{c.name}</p><p className="text-xs text-indigo-300">{c.role}</p></div>
                </div>
                <div className="character-actions opacity-0 group-hover:opacity-100 flex space-x-1 absolute right-2 top-2">
                  <button className="text-indigo-300 hover:text-white" onClick={() => openModal('character', idx)}><i className="fas fa-pencil-alt text-xs"></i></button>
                  <button className="text-indigo-300 hover:text-white" onClick={() => handleDelete('character', idx)}><i className="fas fa-trash-alt text-xs"></i></button>
                </div>
              </div>
            ))}
          </div>
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-indigo-200">Locations</h3>
              <button className="text-indigo-300 hover:text-white" onClick={() => openModal('location')}><i className="fas fa-plus"></i></button>
            </div>
            <div className="space-y-2">
              {locations.map((l, idx) => (
                <div key={idx} className="bg-indigo-800 rounded-md p-2 relative group flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center"><i className="fas fa-map-marker-alt text-sm"></i></div>
                    <div><p className="font-medium">{l.name}</p><p className="text-xs text-indigo-300">{l.desc}</p></div>
                  </div>
                  <div className="character-actions opacity-0 group-hover:opacity-100 flex space-x-1 absolute right-2 top-2">
                    <button className="text-indigo-300 hover:text-white" onClick={() => openModal('location', idx)}><i className="fas fa-pencil-alt text-xs"></i></button>
                    <button className="text-indigo-300 hover:text-white" onClick={() => handleDelete('location', idx)}><i className="fas fa-trash-alt text-xs"></i></button>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-indigo-200">Timeline</h3>
              <button className="text-indigo-300 hover:text-white" onClick={() => openModal('timeline')}><i className="fas fa-plus"></i></button>
            </div>
            <div className="bg-indigo-800 rounded-md p-3">
              <div className="relative">
                <div className="absolute left-3 h-full w-0.5 bg-indigo-600"></div>
                <div className="space-y-4 pl-6">
                  {timeline.map((t, idx) => (
                    <div key={idx} className="relative group">
                      <div className="absolute left-3 w-2 h-2 rounded-full bg-indigo-400 mt-1.5"></div>
                      <p className="text-sm font-medium inline-block">{t.title}</p>
                      <span className="text-xs text-indigo-300 ml-2">{t.desc}</span>
                      <span className="character-actions opacity-0 group-hover:opacity-100 flex space-x-1 absolute right-0 top-0">
                        <button className="text-indigo-300 hover:text-white" onClick={() => openModal('timeline', idx)}><i className="fas fa-pencil-alt text-xs"></i></button>
                        <button className="text-indigo-300 hover:text-white" onClick={() => handleDelete('timeline', idx)}><i className="fas fa-trash-alt text-xs"></i></button>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* 通用弹窗 */}

      {modal.open && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 min-w-[320px]">
            <h3 className="text-lg font-semibold mb-4">{modal.idx !== null ? '编辑' : '新增'}{modal.type === 'character' ? '角色' : modal.type === 'location' ? '场景' : '章节'}</h3>
            <div className="space-y-3">
              {modal.type === 'character' && (
                <>
                  <input className="w-full border px-3 py-2 rounded" placeholder="角色名" value={modalData.name} onChange={e => setModalData({ ...modalData, name: e.target.value })} />
                  <input className="w-full border px-3 py-2 rounded" placeholder="角色身份" value={modalData.role} onChange={e => setModalData({ ...modalData, role: e.target.value })} />
                </>
              )}
              {modal.type === 'location' && (
                <>
                  <input className="w-full border px-3 py-2 rounded" placeholder="场景名" value={modalData.name} onChange={e => setModalData({ ...modalData, name: e.target.value })} />
                  <input className="w-full border px-3 py-2 rounded" placeholder="场景描述" value={modalData.desc} onChange={e => setModalData({ ...modalData, desc: e.target.value })} />
                </>
              )}
              {modal.type === 'timeline' && (
                <>
                  <input className="w-full border px-3 py-2 rounded" placeholder="章节标题" value={modalData.title || ''} onChange={e => setModalData({ ...modalData, title: e.target.value })} />
                  <input className="w-full border px-3 py-2 rounded" placeholder="章节描述" value={modalData.desc || ''} onChange={e => setModalData({ ...modalData, desc: e.target.value })} />
                </>
              )}
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300" onClick={closeModal}>取消</button>
              <button className="px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-700 text-white" onClick={handleSave}>保存</button>
            </div>
          </div>
        </div>
      )}
    </>
  )
};

export default LeftSidebar;
