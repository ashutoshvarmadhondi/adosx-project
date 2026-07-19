import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
  } from "recharts";
  
  import type {
    ReconciliationException,
  } from "../types/api";
  
  type DashboardChartsProps = {
    exceptions: ReconciliationException[];
  };
  
  const CHART_COLORS = [
    "#5b5ce2",
    "#e59b38",
    "#df5d68",
    "#46a37a",
    "#8a65d6",
    "#4e89cc",
  ];
  
  function formatReason(reasonCode: string): string {
    return reasonCode
      .toLowerCase()
      .split("_")
      .map(
        (word) =>
          word.charAt(0).toUpperCase() + word.slice(1),
      )
      .join(" ");
  }
  
  export default function DashboardCharts({
    exceptions,
  }: DashboardChartsProps) {
    const reasonCounts = exceptions.reduce<
      Record<string, number>
    >((counts, exception) => {
      counts[exception.reason_code] =
        (counts[exception.reason_code] ?? 0) + 1;
  
      return counts;
    }, {});
  
    const locationCounts = exceptions.reduce<
      Record<string, number>
    >((counts, exception) => {
      const location =
        exception.location_id ?? "Unknown";
  
      counts[location] = (counts[location] ?? 0) + 1;
  
      return counts;
    }, {});
  
    const reasonData = Object.entries(reasonCounts).map(
      ([reasonCode, count]) => ({
        name: formatReason(reasonCode),
        count,
      }),
    );
  
    const locationData = Object.entries(locationCounts).map(
      ([location, count]) => ({
        location,
        count,
      }),
    );
  
    return (
      <section className="charts-grid">
        <article className="chart-card">
          <div className="chart-card-heading">
            <div>
              <h2>Exceptions by reason</h2>
              <p>Distribution of currently visible findings.</p>
            </div>
          </div>
  
          {reasonData.length > 0 ? (
            <div className="chart-content">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={reasonData}
                    dataKey="count"
                    nameKey="name"
                    innerRadius={62}
                    outerRadius={96}
                    paddingAngle={3}
                  >
                    {reasonData.map((item, index) => (
                      <Cell
                        key={item.name}
                        fill={
                          CHART_COLORS[
                            index % CHART_COLORS.length
                          ]
                        }
                      />
                    ))}
                  </Pie>
  
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
  
              <div className="chart-legend">
                {reasonData.map((item, index) => (
                  <div key={item.name}>
                    <span
                      style={{
                        backgroundColor:
                          CHART_COLORS[
                            index % CHART_COLORS.length
                          ],
                      }}
                    />
  
                    <p>{item.name}</p>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="chart-empty">No chart data available.</p>
          )}
        </article>
  
        <article className="chart-card">
          <div className="chart-card-heading">
            <div>
              <h2>Exceptions by location</h2>
              <p>Concentration of findings across locations.</p>
            </div>
          </div>
  
          {locationData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={locationData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />
  
                <XAxis
                  dataKey="location"
                  tickLine={false}
                  axisLine={false}
                />
  
                <YAxis
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                />
  
                <Tooltip />
  
                <Bar
                  dataKey="count"
                  fill="#5b5ce2"
                  radius={[7, 7, 0, 0]}
                  maxBarSize={55}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">No chart data available.</p>
          )}
        </article>
      </section>
    );
  }