\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{algorithmicx}
\usepackage[ruled]{algorithm}
\usepackage[noend]{algpseudocode}
\usepackage{amsmath}
\usepackage{multicol}
\usepackage{caption}
\usepackage{fullpage}
\usepackage{graphicx}
\usepackage{pgfplots}
\usepackage{tikz}
\usepackage{array}
\usepackage{url}

\pgfplotsset{width=\linewidth,compat=1.9}

\algdef{SE}[DOWHILE]{Do}{doWhile}{\algorithmicdo}[1]{\algorithmicwhile\ #1}%

\newenvironment{Figure}
  {\par\medskip\noindent\minipage{\linewidth}}
  {\endminipage\par\medskip}

\graphicspath{ {image/} }

\title{Optimizing Callout in Unified Ad Markets}
\author{Aman Gupta\thanks{Inmobi Inc.}, S. Muthukrishnan\thanks{Rutgers Univ}, Smita Wadhwa\thanks{Inmobi Inc.}}
\date{July 2016}

\begin{document}

\maketitle

\begin{multicols}{2}
\raggedcolumns

\begin{abstract}
In the past, online ad networks predominantly owned their supply of impressions for ads with publishers and matched it to their 
own demand (advertisers). However, in the past few years, with programmatic ad selling becoming common place, these ad networks are now appealing to demand from multitude of  real time exchanges (RTEs) and demand side platforms (DSPs).  The general approach is to partition the demand into pools (based on type of ads or the demand party). 
An inevitable challenge  is the {\em impedance mismatch} between the marketplace and the demand pools. 
Thus, a central problem is to figure out how to handle each demand request and selectively send requests to demand pool so as to optimize the performance of entire supply. This is the {\em Callout Problem}. 

We present a large scale data analysis and control system that
(a)  continually learns changing traffic patterns, capacities, bids, revenue etc, and 
(b) picks the best slice of traffic to send to each demand pool, subject to their capacity constraints. The optimization  is based on a greedy solution to the underlying knapsack problem which easily adapts as capacities change over time. 
We have implemented and deployed this solution for the callout problem in one of the largest mobile ad marketplaces (InMobi) and has been operational for several months.  In this paper, we will describe the scale of the problem, our solution and our observations from operational experience with it. We believe a well-engineered solution to the Callout problem is essential for many ad networks in the online ad world. 
\end{abstract}

\section{Introduction}

The business of advertising has evolved in a manner that it now can be classified into two prominent verticals - Direct Sales and Real Time Exchanges. Further, there is a variety of the type of ads within each vertical, for e.g., by intent (like Brand promotion, App Download or Online Commerce), media type (like static banner, video) etc. This creates a diversified portfolio of many demand types, which helps reduce risk of revenue variation for the publisher. A natural way to design the market is to segregate these demand types into different \emph{pools}, each bidding independently, and let these bidders compete in an unified auction for maximum competition, and reduced ad serving latency. The supply can remain agnostic of various demand types, while the market design tries to optimize revenue for the publisher.

In practice, though, it is often the case that each demand type develops some affinity with a subset of all available supply, and it is a wasteful use of machine resources to expose all supply to each demand pool. Thus, an essential component of such an unified marketplace is a layer, which we have named Callout, that prioritizes supply for each demand pool such that the resource usage of each demand pool can be optimized while having only a negligible impact on revenue.

In the rest of the paper we describe our design of the Callout layer. The following sections contain:
\begin{itemize}
    \item A detailed description of the Callout problem, together with the constraints of demand types. We also design and present an algorithm that picks the best slice of traffic to send to each demand, subject to their capacity constraints. The optimization  is based on a greedy solution to the underlying knapsack problem which easily adapts as capacities change over time. Further, the algorithm continually learns and adapts 
    \item We have an operational implementation of this algorithm in a  large mobile ad network (InMobi) and it has been in use for a few months. We report on our experience and present empirical analysis of our Callout algorithm. 
\end{itemize}

The Callout problem had been previously studied in theory~\footnote{\url{http://arxiv.org/pdf/1002.3102.pdf}}, where they modeled the problem as one of queueing, and used a sophisticated primal-dual approach to get approximation algorithms subject to expected case constraints. In reality, the distributions of bids, revenue, traffic, clicks and other parameters vary a lot across the pools and time, and we need an approach that adapts to changing characteristics. We model the problem in such a way that simple knapsack based algorithm suffices and is flexible enough to be adapted as system changes, as our description and results will show. The general context of Callout arises not only in ad networks, but also in ad exchanges.~\footnote{See \url{http://www0.cs.ucl.ac.uk/staff/w.zhang/rtb-papers/rtb-survey.pdf} for example for discussion of related work.}

\section{The Callout problem}

\subsection{The Central Marketplace}

A modern ad network is a complicated marketplace. On the supply side, there are many channels of supply, such as direct sales channel, the Real Time Bidding (RTB) supply channel, and the OEM channel where the device manufacturer is a publisher, pioneered by the likes of Amazon when it started selling ad supported Kindles at cheaper prices. All these channels are further categorized by the platform, which are the desktop and mobile. Most publishers exist only on one of the platforms, and the ad experiences are quite different on different platforms, which impacts the marketplace as well, constraining supply and demand and also differing greatly in pricing. Examples of sources of supply include many major online websites like Wired or CNET (desktop), apps of various categories like Line chat app, Flipboard news app or Subway Surfers game app (mobile), and companies with SSP products like Doubleclick for Publishers and Rubicon Project (RTB).

The demand side has a similar structure. There are multiple types of advertisers based on the intended action, like brand promotion, app download, lead generation, online commerce. Each of these advertisers can come through multiple channels like direct sales or as RTB demand. The platform (desktop vs mobile) splits all demand in a manner identical to how it splits the supply. Advertisers include major brands like Nike or Ford Motor Company (Brand), apps like Game of War and Clash of Clans (App download), and commerce sites like Target and Walmart.

We assume that our marketplace consists of many supply channels and many demand pools (bidders). The actual component with whom both the supply and demand pools interact is called the Unified MarketPlace (UMP). For each ad slot available for sale, the publisher requests for an ad to the UMP, which invites a bid from the demand pools in realtime. The demand pools provide a CPM bid for that ad slot to the UMP, which then chooses the highest bidder's ad in the \emph{unified auction}, to be shown in the ad slot.

\begin{figure*}[ht]
  \centering
  \includegraphics[width=\textwidth]{central_mp}
  \caption[mp]{The marketplace structure of a modern ad network}
  \label{fig:centralmp}
\end{figure*}

\subsection{Callout Problem}

The total number of requests received by UMP is represented by $R(t)$, where $t$ is the time, and is measured in ad requests per second (qps). The UMP service capacity is always greater than $R(t)$. The entirety of all ad requests are segmented in $p$ sets, $S_{1}, S_{2}, ..., S_{p}$, using request parameters as the dimensions of buckets in which to put all requests. The request parameters can be the publisher id, country, device operating system, type of ad slot (Banner, Interstitial etc.) and so on. 

We have $m$ demand pools, each with a maximum serving capacity of $q_{j}(t)$ qps. UMP is required to limit traffic sent to demand pool $j$ to $q_{j}(t)$, i.e., if UMP forwards more requests to the demand pool, it will start seeing failures such as time-outs. The actual traffic sent by UMP to the demand pool is denoted by $\phi_{j}(t)$. Note that the capacity is a function of time, which is a by product of modern service infrastructure where the total machine resources are dynamically allocated based on current requirements of each service. We will also assume that the forecasting $q_{j}(t)$ is not possible, as the factors controlling the capacity are outside the scope of the marketplace to model. For this problem to be interesting, we would want that $R(t) > q_{j}(t)$, at least for some periods of time in a day (otherwise we can send all ad requests to the demand pool all the time). 

Demand pools also have a mechanism to manually supply whitelist (and blacklist) rules by which some parts of supply must (or never) be forwarded to the demand pools. Whitelists are required when there is a private deal between a publisher and the advertiser, which the ad network is facilitating. Blacklists could be required, for example, to avoid showing an app download ad on a competitive app. This allowance has an impact on the solution, for e.g., having a whitelist means that a variable amount of demand pool's serving capacity is taken up by the whitelisted supply. The UMP must always keep a measure of that and then optimize supply choice for the remaining capacity.

The restrictions forced upon us by the physical limitations of infrastructure are quite relevant to the problem, and we assume a generic layout for an implementation of ad marketplace. There is a single datacenter where both the UMP and the demand pools are running as services. The number of nodes each service occupies is variable over time. The UMP has a logging system which logs the request and auction details of each request, which are transported and stored in a distributed file system (like HDFS). There is a distributed analysis framework (like MapReduce or Apache Spark) available which can work on these logs, and the result of that analysis can be transported back to all nodes of any service. This feedback loop is not realtime, and delays are in the order of tens of minutes.

Let's say UMP receives ad requests $\alpha_{1}, \alpha_{2}, ..., \alpha_{n}$ in a given time interval $[t_1, t_2]$. There exists a strictly monotonic increasing function $T \colon \{1,2,...,n\} \to [t_1, t_n]$, which represents the time at which we received the request. For every request $\alpha_{i}$, a set $D_{i} \subseteq \{1,2,...,m\}$ represents the demand pools to be called on that request. If $\epsilon$ is a very small number, then we can define the number of requests sent to the demand pool $j$ as follows:

$$ \phi_{j}(t) = \left\vert{\{i : j \in D_{i}, T^{-1}(t) \leq i \leq T^{-1}(t + \epsilon) \}}\right\vert  $$

We assume that bidders bid their value in a second price auction, where each bidder $j$ receives a value from the probability function $F_{j,k}(x)$ for every request coming from segment $S_k$. Each request from segment $S_k$ also has a reserve price set at $f_k$. Then the revenue earned on request $\alpha_{i}$ is defined by:

$$ \chi(i) = second\_highest(\{ X_{j,k} : j \in D_i \} \cup \{ f_k, 0 \})$$

where $X_{j,k}$ represents the random variable for the bidder's value.

The callout algorithm must choose $D_i$ for each request $\alpha_i$ so that we:

$$ maximize \sum_{i=1}^{n} \chi({i}) $$

such that

$$ \phi_{j}(t) \leq q_{j}(t), \forall j \in \{1,2,...,m\}, \forall t \in [t_1, t_2] $$

\section{Solving the callout problem}
The main idea to the solution is for UMP to associate a \emph{value} with each ad request, one for every demand pool. This value encapsulates factors like probability of bid, the bid amount etc. The capacity of each demand pool can then be mapped to a \emph{value threshold} using which the UMP filters away all the requests whose value is below that threshold, for that demand pool.

To start with, we denote the number of requests from each of the supply segments $S_k$ by $r_k(t)$, such that $R(t) = \sum_{k=1}^p r_k(t)$. In the solution, we would need to know the function $r_k(t)$ for a time in future, thus this becomes the forecasted traffic from the supply segment $S_k$.

For each segment $S_k$, and demand pool $j$, let $\nu_{j,k}$ denote the value of all requests in that supply segment for the $j^{th}$ demand pool. The value is defined by:

$$ \nu_{j,k} = 
\begin{cases}
\mathbf{E}(X_{j,k}), \text{if } \mathbf{E}(X_{j,k}) \geq f_k\\
0, \text{otherwise}
\end{cases} $$

Given this structure, we can now map the problem to 0-1 Knapsack problem, for a time instant $t$

\begin{itemize}
    \item The demand pool is the knapsack with capacity $q_j(t)$.
    \item Each supply segment $S_k$ is an item available to fill the knapsack, with value $\nu_{j,k}$ and weight $r_k(t)$.
\end{itemize}

Of course, finding an optimal solution to 0-1 Knapsack problem is an NP complete problem. Practically, we use the greedy solution of the 0-1 Knapsack problem, which means that for any segment $S_{k^*}$ that is part of the solution, all other segments $\{S_k : \nu_{j,k} \geq \nu_{j,k^*}\}$ are also part of the solution. This allows us to define a threshold value, such that any segment with value above the threshold is included in the solution. For every demand pool $j$, We reorder the segments $S_k$ so that $\nu_{j,k} \geq \nu_{j,k+1}, 1 \leq k \leq p-1$. The value threshold function is defined as:

$$ \nu_j^{\tau}(t, x) = \nu_{j, k^*}, s.t. $$
$$ \sum_{k=1}^{k^*} r_k(t) \leq x $$
$$ \sum_{k=1}^{k^* + 1} r_k(t) > x $$

There is the assumption that for $r_1(t) \leq q_j(t), \forall t \in [t_1, t_2]$, which is a fair assumption to make. Its easy to define the the allocation $D_i$ now:

$$ D_i = \{j : \nu_{j,k} \geq \nu_j^{\tau}(t, q_j(t)), \alpha_i \in S_k \} $$
$$ \text{ where } t = T(i) $$

\section{Implementation}

\alglanguage{pseudocode}
\begin{algorithm*}
\small
\caption{Compute value threshold Function}
\label{Algorithm:capacityThreshold}
\begin{algorithmic}[1]
\Procedure{$\mathbf{getValueThresholdFunction}$}{$\{S_{k}\}$, $\{\nu_{j,k}\}$, $\{r_k(t)\}$, demand pool $j$, $W_j$, $B_j$}
    \State sort($\{S_{k}\}$, comparator = $\nu_{j, k_1} > \nu_{j, k_2}$)
    \Comment \emph{descending on value}
    \State p = $|\{S_{k}\}|$
    \For {$i = 1 \to 24$}
        \State totalQps = 0
        \State segmentQps = 0
        \State k = 1

        \While {$k \leq p$}
            \State valueThresholdFunction(t, totalQps) = $\nu_{j, k}$
            \State totalQps = totalQps + 10
            \State segmentQps = segmentQps + 10
            \If {segmentQps $> r_k(t)$}
                \Do
                    \State k = k + 1
                \doWhile{$S_k \in W_j$ or $S_k \in B_j$}
                \State segmentQps = 0
            \EndIf
        \EndWhile
    \EndFor

\EndProcedure
\end{algorithmic}
\end{algorithm*}

As described in section 2.2 there are a lot of restrictions that the real infrastructure enforces on us. Chief among them are:
\begin{itemize}
    \item The demand pool capacity $q_j(t)$ for the future is an unknown, and can change anytime. 
    \item The delay in feedback loop from logging to data analysis and back to UMP is large and in tens of minutes. We cannot keep serving the demand pool the same amount of traffic as before when its capacity changes, and only update our traffic allocation when the feedback is complete.
\end{itemize}

This is why we defined the value threshold function $\nu_j^{\tau}$ as a function of both time and demand pool capacity. If this function is available to UMP at request time, then it can make the decision for any value of current demand pool capacity.

In section 2.2, we also discussed the presence of whitelists and blacklists. We can define both of these as subsets of the power set of the set of supply segments:

$$ W_j \subseteq \mathbf{P}(\{S_1, S_2,..., S_p \}), s.t. $$
$$ j \in D_i, \forall \alpha_i \in S_k, \forall S_k \in W_j $$

$$ B_j \subseteq \mathbf{P}(\{S_1, S_2,..., S_p \}), s.t. $$
$$ j \not\in D_i, \forall \alpha_i \in S_k, \forall S_k \in B_j $$

These have to be taken into account when computing the value threshold function. For a supply segment in whitelist of a demand pool $j$, the callout algorithm must include the demand pool $j$, and a certain part of the capacity is taken by these segments. The callout algorithm computes the value threshold function ignoring these whitelisted segments, and UMP assumes that the capacity of demand pool $j$ is reduced by the amount of traffic from these whitelisted segments. Similarly, for a supply a segment in the blacklist, the callout algorithm must exclude the demand pool $j$, and this doesn't impact the capacity of the ad pool. The value threshold function can simply ignore these segments as well.

Based on this reasoning, the value threshold functions are redefined as:

$$ \nu_j^{\tau}(t, x) = \nu_{j, k^*}, s.t. $$
$$ \sum_{\substack{k=1\\
            S_k \not\in W_j\\
            S_k \not\in B_j}}^{k^*}
            r_k(t) \leq x
$$
$$ \sum_{\substack{k=1\\
            S_k \not\in W_j\\
            S_k \not\in B_j}}^{k^* + 1}
            r_k(t) > x
$$

If we denote the whitelisted traffic as $r^W(t)$, the updated allocation is:

$$ D_i = \{j : \nu_{j,k} \geq \nu_j^{\tau}(t, q_j(t) - r^W(t)), \alpha_i \in S_k \} $$
$$ \text{ where } t = T(i) $$

This allocation assumes that $r^W(t) < q_j(t)$, which makes sense in practical situations.

For implementation, we need to make the variables of time and traffic qps discrete. We define time as the \emph{hour of the day} and measure qps as integers whose values are multiples of 10. The algorithm to compute the value threshold function is shown in Algorithm \ref{Algorithm:capacityThreshold}.

For UMP to make its decision on each request, it needs to know the value of each segment, the capacity threshold map, and the current capacity of each demand pool. When UMP receives an ad request, it looks up the value of segment using request parameters, and forwards the request to the demand pool if the value is greater than the value threshold based on current capacity of the ad pool.

\subsection {Hadoop pipeline}

Our source of data in the hadoop pipeline are the auctions logs published by the UMP. These logs contain the request parameters for each ad slot, the list of demand pools who bid for that slot along with the bid value, and the winner and charged price from the unified auction, and the timestamp of the event. Using these logs, we need two outputs:


\alglanguage{pseudocode}
\begin{algorithm*}
\caption{valueThreshold Map Reduce implementation}
\label{Algorithm:valueThresholdMR}
\begin{algorithmic}[1]
\Procedure{$\mathbf{segmentValueMap}$}{$S_{k}$, $j^*$, $\nu_{j^*, k}$}
    \State output($(j^*), (S_{k}, \nu_{j^*, k}, null)$)
\EndProcedure

\Procedure{$\mathbf{trafficForecastMap}$}{$S_{k}$, $r_{k}(t)$}
    \For {$j = 1 \to m$}
        \State output($(j), (S_{k}, null, r_{k}(t))$)
    \EndFor
\EndProcedure

\Procedure{$\mathbf{valueThresholdReduce}$}{$(j^*)$, $[S_{k}, \nu_{j^*,k}, r_{k}(t)]$}
    \State output($(j^*), getValueThresholdFunction([S_{k}], [\nu_{j^*}, k], [r_{k}(t)], j^*, W_j, B_j$)
\EndProcedure

\end{algorithmic}
\end{algorithm*}

\begin{enumerate}
    \item The set $ \{(S_{k}, j, \nu_{j,k}) : 1 \leq k \leq p, 1 \leq j \leq m \} $, which is the value of the supply segment to each demand pool.
    \item The set $ \{(S_{k}, t, r_{k}(t)) : 1 \leq k \leq p \} $, which is the traffic forecast for each supply segment at any time.
\end{enumerate}

Let $\rho_{j,k}$ represent the traffic from segment $S_k$ which goes to demand pool $j$. Given the definition of $\nu_{j,k}$ from section 3, item 1 is a simple aggregate operation over demand pool bids to get $\sum \chi_{j,k}$ and $\sum \rho_{j,k}$ over a period of time $\Delta t$, for each $S_{k}$ and demand pool $j$. The period of $\Delta t$ is usually equal to a few days, and we maintain a moving window aggregate of fixed length = $\Delta t$. Since the raw data logs are updated every ten minutes, it is impractical to compute a multi day aggregate so frequently. Thus, our moving window aggregate is maintained by adding the latest data of last ten minutes to the current aggregate, while subtracting the data for the duration of 10 minutes which no longer lies within the new window.

For item 2, we can maintain simplicity by using the average historical traffic as our forecast, or use more sophisticated methods to forecast traffic. The accuracy requirement of the forecast is decided by how tightly are we trying to manage resources for each demand pool. In our case, we use historical average over a few days for traffic forecast. This then becomes a moving aggregate similar to that in item 1, and we use an identical approach to maintain the moving aggregate.

We still need to run the code outlined in Algorithm \ref{Algorithm:capacityThreshold} to get the data that UMP consumes. This needs both item 1 and item 2 above, and a Map Reduce can be written as shown in Algorithm \ref{Algorithm:valueThresholdMR} (with two mappers and one reducer). Since the number of demand pools $j$ and hours in a day are very small numbers when compared to the number of segments $p$, the benefit of parallelization are small. For us, it turns out that the single process implementation of Algorithm \ref{Algorithm:valueThresholdMR} works almost as fast as an MR version, and we chose to run it as a single process eventually.

\section{Results and Lessons}

We deployed our implementation of Callout in October 2015, and since then have been maintaining it. Before deployment, we spent a lot of time to analyze its impact on the market. And since then we have been keeping an eye on its performance. This section discusses the impact on Callout on our marketplace.

In the following results, we take an example of one demand pool (we'll call it \textbf{PoolA}), which is quite an important contributor to InMobi's revenue, but bids only on certain pockets of supply. This makes it a perfect subject to the Callout optimization algorithm.

\subsection{Callout vs Random drop}

We devised a test which set the capacity of demand pool \textbf{PoolA} at approximately half of the peak UMP traffic. Then we compare the two methods: the callout algorithm and traffic randomly dropped (with uniform probability on each request) such that it meets the new capacities, and compared the revenue impact of this traffic drop. We also had a control bucket where we dropped no traffic, to see the max revenue \textbf{PoolA} could have made with all of supply.

For measuring the impact of random drop, we can break a time period into many small slices. Since this algorithm drops traffic without care, if we drop $50\%$ of traffic randomly, our revenue impact is also equal to $50\%$ within any of that time slice. If you aggregate over a large period of time, the revenue impact is equal to

$$ \text{revenue loss ratio} = \frac{\text{requests dropped}}{\text{total requests}} $$

The results of this experiment are shown in figure \ref{fig:random} below. As you can observe, the total traffic sent to \textbf{PoolA} is reduced by $29\%$ but the revenue drop is only $2.6\%$. This result is $11.1$ times better than dropping traffic randomly. Secondly, the Bid rate and Avg CPM of the demand pool both see an increase. This is consistent with our expectations, as we would send traffic from high value segments to fill the reduced capacity.

\begin{Figure}
  \centering
  \begin{tikzpicture}
  \begin{axis}[
    ymin=0,
    ybar,
    legend style={at={(0.5,-0.15)},
      anchor=north,legend columns=-1},
    ylabel={Percent},
    symbolic x coords={Traffic,Revenue,Bid Rate,Avg CPM},
    xtick=data,
    nodes near coords,
    nodes near coords align={vertical},
    every node near coord/.append style={font=\tiny},
    ]
  \addplot coordinates {(Traffic,100) (Revenue,100) (Bid Rate,100) (Avg CPM, 100)};
  \addplot coordinates {(Traffic,71) (Revenue,97.4) (Bid Rate,134) (Avg CPM, 106.1)};
  \legend{Full Capacity, Reduced capacity}
  \end{axis}
  \end{tikzpicture}
  \captionof{figure}{Callout vs Random drop}
  \label{fig:random}
\end{Figure}



\subsection{Callout vs team of experts}
As mentioned in the beginning of this section, sending $100\%$ was too costly for the demand pool \textbf{PoolA}, as majority of the UMP traffic was not bid at by the demand pool. Hence, before callout was launched, the supply selection for the demand pool \textbf{PoolA} was done manually by a business team who monitored the marketplace constantly. We ran an experiment to compare the performance on supply segments chosen by Callout to the performance on about $55,000$ supply segments chosen by that team.

Figure \ref{fig:expert} shows the results of this experiment. It turns out that the team did a good job of making sure that all traffic sent to the demand pool was actually valuable for it. But, on the other hand, due to the sheer scale and variation of amount of supply at InMobi, they were not able to find out all supply segments which were valuable to the demand pool. Callout helped increase revenue by a significant $14.6\%$, but in doing it used $46\%$ more capacity due to the $8,500$ more supply segments which Callout opened for \textbf{PoolA}. As can be inferred by reduced Avg CPM, the bids on these $8,500$ new segments were lower than on the existing traffic.

A side effect of opening more traffic for demand pool \textbf{PoolA} is increased competition on the supply, as there are other ad pools bidding on the same supply. The total revenue from all these $63,500$ supply segments went up $8.5\%$, with Avg CPM seeing gains of $5.7\%$.

\begin{Figure}
  \centering
  \begin{tikzpicture}
  \begin{axis}[
    ymin=0,
    ybar,
    legend style={at={(0.5,-0.15)},
      anchor=north,legend columns=-1},
    ylabel={Percent},
    symbolic x coords={Traffic,Revenue,Bid Rate,Avg CPM},
    xtick=data,
    nodes near coords,
    nodes near coords align={vertical},
    every node near coord/.append style={font=\tiny},
    ]
  \addplot coordinates {(Traffic,100) (Revenue,100) (Bid Rate,100) (Avg CPM, 100)};
  \addplot coordinates {(Traffic,146) (Revenue,114.6) (Bid Rate,100.4) (Avg CPM, 89.8)};
  \legend{Manual selection, Callout}
  \end{axis}
  \end{tikzpicture}
  \captionof{figure}{Callout vs team of experts}
  \label{fig:expert}
\end{Figure}

\subsection{Learning}
An important aspect of any such algorithm is continued learning, which is required to make sure we keep evaluating all of our supply for its value to each demand pool. In our Callout implementation we used a varation of \emph{epsilon greedy} learning approach: we partitioned our supply segments into \emph{high value}, for those segments with value above the value threshold, and \emph{low value} for all other segments. $10\%$ of capacity was set aside for the low value segments (denoted by \textbf{L}), where the probability that a request from low value segments will be forwarded to the demand pool being equal to:

$$ \frac{0.1q_j(t)}{\sum_{S_k \in \textbf{L}} r_k(t)} $$

To compute the threshold for high value segments, we use effective capacity $ = 0.9q_j(t)$. All results from previous sections use this implementation.

To illustrate the importance of learning, we found the number of segments which overlapped among high value segments callout selected one week apart, capacities remaining the same. As shown in figure \ref{fig:learningsegs}, $23,645$ new segments become high value segments for the demand pool \textbf{PoolA}. Of these, $19,732$ were not even revenue making for $PoolA$ in the previous week. Even in the top $10$ segments (by revenue), we noticed that only $6$ segments persisted across the week, and 4 new segments entered the top 10.

\begin{Figure}
  \centering
  \begin{tikzpicture}
  \def\radius{2cm}
  \def\mycolorbox#1{\textcolor{#1}{\rule{2ex}{2ex}}}
  \colorlet{colori}{blue!70}
  \colorlet{colorii}{red!70}

  \coordinate (ceni);
  \coordinate[xshift=\radius*1.2] (cenii);

  \draw[fill=colori,fill opacity=0.5] (ceni) circle (\radius);
  \draw[fill=colorii,fill opacity=0.5] (cenii) circle (\radius);
  
  \draw  ([xshift=-20pt,yshift=20pt]current bounding box.north west) 
  rectangle ([xshift=20pt,yshift=-20pt]current bounding box.south east);

  \node[yshift=10pt] at (current bounding box.north) {Number of high value segments for \textbf{PoolA}};


  \node at ([xshift=0.5\radius,yshift=-0.7\radius]current bounding box.south) 
  {
    \begin{tabular}{@{}lr@{\,=\,}c@{}}
    \mycolorbox{colori!50} & Week1 & 66,832 \\
    \mycolorbox{colorii!50} & Week2 & 71,713 \\
    \end{tabular}
  };

\node[xshift=-.5\radius] at (ceni) {$18,764$};
\node[xshift=.5\radius] at (cenii) {$23,645$};
\node[xshift=1.2\radius] at (ceni) {$48,068$};
\end{tikzpicture}

  \captionof{figure}{Change of segments in one week}
  \label{fig:learningsegs}
\end{Figure}

Finally, we computed the regret due to learning traffic. Regret is dependent on capacity; if we set capacities very low, then $10\%$ of traffic has more value compared to the case where we set high capacities. Figure \ref{fig:regret} shows the regret $\%$ as a function of capacity for demand pool \textbf{PoolA}.

\begin{Figure}
  \centering
  \begin{tikzpicture}
	\begin{axis}[
		xlabel=Capacity in qps,
		ylabel=Regret $\%$]
	\addplot[color=red,mark=x] coordinates {
        (2000.0,6.446445654966444)
        (4000.0,6.1332302576169641)
        (6000.0,5.294279220502581)
        (8000.0,3.786651660175032)
        (10000.0,3.4462262018352424)
        (12000.0,2.5418215840961107)
        (14000.0,2.446914752374779)
        (16000.0,1.705765585566316)
        (18000.0,1.1714571231119362)
        (20000.0,1.029126992416559)
        (22000.0,0.5180114182485797)
        (24000.0,0.37641347248887685)
        (26000.0,0.12036910773557709)
        (28000.0,0.012895570256494225)
        (30000.0,0.000973840915631074)

	};
	\end{axis}
  \end{tikzpicture}
  \captionof{figure}{Regret due to learning}
  \label{fig:regret}
\end{Figure}

\subsection{Multiple data centers}
We have multiple data centers across the world to optimize latency at the device, and every location in the world is mapped to exactly one datacenter. Each demand pool will have a different capacity in each datacenter. How do we change the decision making so that the UMP honors the capacity requirements at each datacenter?

One way is to consider the datacenter itself a parameter in the definition of our supply segment. UMP service in each datecenter can then concentrate only on supply in its own datacenter.

At InMobi, the mapping from location to datacenter is dynamic, and this can lead to the issue that the UMP wants to serve requests from a segment to a demand pool, but requests from that segment is no longer coming to the same datacenter. Instead, we let UMP continue to make the decision at the global level: It calculates is value threshold using the sum of capacities from all datacenters frome each adpool. But this means that each demand pool's traffic in a datacenter is determined only by the global capacity and the location to datacenter mapping. Local capacity of each demand pool becomes a dependent variable instead of an independent variable. We accept this, and this approach helps us manage revenue vs infrastructure costs better and avoids issues arising from dynamic traffic mapping.

For the case of \textbf{PoolA}, if we set total capacity = 30K qps, we see the following distribution of traffic across our data centers:
\begin{center}
 \begin{tabular}{||c c c||} 
 \hline
 DC & QPS & Revenue $\%$ \\ [0.5ex] 
 \hline\hline
 1 & 7.5K & 27.6 \\ 
 \hline
 2 & 8.4K & 22.0 \\
 \hline
 3 & 4.8K & 3.1 \\
 \hline
 4 & 9.3K & 47.3 \\ [1ex]
 \hline
\end{tabular}
\end{center}

The different revenue to traffic ratios reflect the value of ads in different regions.

\subsection{Traffic forecast accuracy}
Throughout this paper, we have assumed that we have a perfect supply forecast available for each segment. In reality, forecasting traffic accurately is a very hard problem. Thus, we would like to know the impact of forecast error on the revenue, and see if putting effort into improving forecasts is worth the effort.

The forecast errors manifest themselves into revenue loss in the following way: We assume that some segments are selected for a demand pool, for the capacity. In reality, those segments may:
\begin{itemize}
  \item collectively contribute to traffic which is less than the capacity. In this case, we could have included more segments, and increased our revenue.
  \item collectively contribute to traffic which is higher than the capacity. In this case, we drop any traffic over capacity randomly, and thus the revenue lost is equal to the amount of traffic dropped randomly.
\end{itemize}

This means that forecast errors such that total expected traffic from a set of segment differs from reality are the cause of revenue loss.

\section{Concluding Remarks}

The need for Callout arised naturally as InMobi  (like other ad networks) looked to diversify its demand across multiple channels and creating a Unified MarketPlace for all the channels. We formulated the problem in a manner which meets the requirements of business. We provide a solution which, in addition to solving the problem as defined theoretically, also takes care of practical infrastructure constraints like frequent and unpredictable demand pool capacity changes, delays in the data feedback loop, and segmentation of supply due to multiple datacenters. In the end, we have a robust implementation that improves on the state-of-the-art handcoded method in terms of revenue and efficiently learns the changing value of the supply. 

There are several issues that we will be good to formalize and study theoretically in the future. For example, we do not have a good model when we optimize based on expected parameters but really care about realized bids. We have not studied the impact of correlated bids of multiple demand pools (except for observing increases in revenue and average CPM due to increased competition). We will be studying the correlation of the bids across pool empirically, but how to address the Callout problem taking into account the 
correlations is interesting.

\end{multicols}

\end{document}
