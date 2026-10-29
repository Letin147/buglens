export default function Bug2() {
  return (
    <main className="bug2-page">
      <h1>商品参数对比</h1>
      <div className="spec-grid">
        <section className="spec-card">
          <h2>标准版 · SKU 编号</h2>
          <p>
            SKU2026XT9000SUPERULTRACOMPACTWIRELESSHEADPHONEMODELPLATINUMEDITIONSERIALNUMBER000123456789ABCDEF
          </p>
          <p>本版本支持蓝牙 5.4 与主动降噪，适合日常通勤使用。</p>
        </section>
        <section className="spec-card">
          <h2>旗舰版 · SKU 编号</h2>
          <p>
            FLAGSHIP-HIRES-AUDIO-CODEC-LDAC-APTX-ADAPTIVE-DUAL-DRIVER-UNIT-TITANIUM-DIAPHRAGM-2026
          </p>
          <p>本版本额外支持 Hi-Res 双认证与无线充电收纳盒。</p>
        </section>
      </div>
    </main>
  );
}
