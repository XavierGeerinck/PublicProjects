using Microsoft.ML.Data;

namespace ModuleFilterCar.Models
{
    public class CarPointSpeedPrediction
    {
        [ColumnName("Score")]
        public float Speed_MPH;
    }
}