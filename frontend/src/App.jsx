import React from 'react';
import Header from './components/Header';
import LeftSidebar from './components/LeftSidebar';
import MainContent from './components/MainContent';
import RightSidebar from './components/RightSidebar';
import OutlinePanel from './components/OutlinePanel';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    // 可以上报日志
    // console.error('ErrorBoundary:', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return <div style={{color: 'red', padding: 24}}>页面发生异常：{this.state.error?.message || '未知错误'}<br/>请检查富文本内容格式或刷新页面重试。</div>;
    }
    return this.props.children;
  }
}

const App = () => {
  // 全局上下文状态
  const [characters, setCharacters] = React.useState([]);
  const [locations, setLocations] = React.useState([]);
  const [timeline, setTimeline] = React.useState([]);
  const [selectedStyle, setSelectedStyle] = React.useState(null);
  const [outline, setOutline] = React.useState(null);

  // 左侧栏回调
  const handleCharactersChange = (list) => setCharacters(list);
  const handleLocationsChange = (list) => setLocations(list);
  const handleTimelineChange = (list) => setTimeline(list);

  // 右侧栏风格回调
  const handleStyleChange = (style) => setSelectedStyle(style);
  // 大纲回调
  const handleOutlineChange = (outlineObj) => setOutline(outlineObj);

  return (
    <ErrorBoundary>
      <div className="flex h-screen overflow-hidden">
        <LeftSidebar
          visible={true}
          toggleLeft={() => {}}
          characters={characters}
          locations={locations}
          timeline={timeline}
          onCharactersChange={handleCharactersChange}
          onLocationsChange={handleLocationsChange}
          onTimelineChange={handleTimelineChange}
        />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-hidden flex">
            <div className="w-[420px] min-w-[320px] max-w-[520px] border-r border-gray-200 overflow-y-auto bg-gray-50">
              <OutlinePanel outline={outline} onOutlineChange={handleOutlineChange} />
            </div>
            <MainContent
              characters={characters}
              locations={locations}
              timeline={timeline}
              style={selectedStyle}
              outline={outline}
            />
            <RightSidebar
              visible={true}
              toggleRight={() => {}}
              onStyleChange={handleStyleChange}
              selectedStyle={selectedStyle}
            />
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default App;
