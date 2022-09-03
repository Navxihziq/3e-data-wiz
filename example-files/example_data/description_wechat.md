- level 1和level2是类似于data那个Excel里两个sheet画level的东西
- timeslicecheckandmarginal我如果没有理解错我们的模型是有两个用处
	1. 每个省份内，加总每个技术（对应tech group应该也是）在每个S,T的组合应该的level 1+level2里面的level等于这里的level
	写成数学公式应该是这样：sum(技术, (level1_技术+level2_技术, S,T))= timeslicecheckandmarginal-level(S,T)
	2. 然后第二个用处是这个文件的marginal是要画的marginal

- 然后annualcheck的作用是，每个技术（组）在每个S,T的level都加起来之后，乘8760/72，应该等于这里的每个技术组的level