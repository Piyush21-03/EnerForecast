export function Skeleton({ className = "", style = {} }) {
  return <div className={`skeleton ${className}`} style={style} />;
}

export function SkeletonCard() {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <Skeleton style={{ width: 100, height: 16 }} />
        <Skeleton style={{ width: 24, height: 24, borderRadius: "50%" }} />
      </div>
      <Skeleton style={{ width: "60%", height: 32, marginBottom: 8 }} />
      <Skeleton style={{ width: "40%", height: 14 }} />
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
        <Skeleton style={{ width: 140, height: 20 }} />
        <Skeleton style={{ width: 120, height: 28, borderRadius: 8 }} />
      </div>
      <Skeleton className="skeleton-chart" />
    </div>
  );
}
