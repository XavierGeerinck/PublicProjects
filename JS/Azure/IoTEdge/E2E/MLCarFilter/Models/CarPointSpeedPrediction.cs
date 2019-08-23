using Microsoft.ML.Data;

namespace MLCarFilter.Models
{
    public class CarPointSpeedPrediction
    {
        [ColumnName("Score")]
        public float Speed_MPH;
    }
}